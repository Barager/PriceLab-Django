from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from decimal import Decimal 
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import uuid
from background_task import background


from .models import Experiment
from .models import User
from .forms import MetaInfoForm, SegmentationForm, AnalysisForm

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()
    
class AnalysisCsvImportForm(forms.Form):
    csv_upload = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_upload'].label = 'CSV Upload'

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    form = MetaInfoForm
    
    def save_model(self, request, obj, form, change):
        obj.save()
        
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()

    
    def analysis(self, request, object_id):
        experiment = self.get_object(request, object_id)
        form = AnalysisForm(instance=experiment)

        if request.method == 'POST':
            form = AnalysisForm(request.POST, instance=experiment)

            if form.is_valid():
                experiment.save()
                
                # Extract selected tests from the form
                selected_tests = form.cleaned_data.get('selected_tests', [])
                
                # Continue with the form processing as before
                form.save()
                
                
                messages.success(request, 'Analysis details updated successfully.')

                print("Form saved successfully.")
                print("Redirecting to changelist.")

                return redirect(reverse('admin:experiments_experiment_changelist'))

        return render(
            request,
            'admin/experiments/experiment/analysis_form.html',
            {'form': form, 'experiment': experiment},
        )


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/segmentation/',
                self.admin_site.admin_view(self.segmentation),
                name='segmentation',
            ),
            path(
                '<path:object_id>/analysis/',
                self.admin_site.admin_view(self.analysis),
                name='analysis',
            ),
            path(
                '<path:object_id>/segmentation/',
                self.admin_site.admin_view(self.segmentation),
                name='segmentation',
            ),
            
        ]
        return custom_urls + urls
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        experiment = Experiment.objects.get(id=object_id)
        # Call the logic from Experiment.save to preselect users
        experiment.save()
        extra_context['preselected_users'] = {
            'treatment_group': list(experiment.treatment_group.values_list('id', flat=True)),
            'control_group': list(experiment.control_group.values_list('id', flat=True)),
        }
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def remaining_days(self, obj):
        current_date = timezone.now()
        end_date = obj.start_date + timedelta(days=obj.duration_days)
        remaining_days = (end_date - current_date).days
        return remaining_days

    remaining_days.short_description = 'Days Left'

    

    def segmentation(self, request, object_id):
        experiment = self.get_object(request, object_id)
        form = SegmentationForm(instance=experiment)

        if request.method == 'POST':
            form = SegmentationForm(request.POST, instance=experiment)
            if form.is_valid():
                form.save()
                
                experiment.ready_for_analysis()
                messages.success(request, 'Segmentation details updated successfully.')
                return redirect(reverse('admin:experiments_experiment_changelist'))

        return render(
            request,
            'admin/experiments/experiment/segmentation_form.html',
            {'form': form, 'experiment': experiment},
        )


    def segmentation_button(self, obj):
        url = reverse('admin:segmentation', args=[obj.id])
        return format_html('<a class="button" href="{}">Segment</a>', url)

    segmentation_button.short_description = 'Segmentation'

    
    def ready_for_analysis(self, obj):
        return obj.ready_for_analysis()

    def analysis_button(self, obj):
        if obj.ready:
            url = reverse('admin:analysis', args=[obj.id])
            return format_html('<a class="button" href="{}">Analyse</a>', url)
        else:
            return format_html('<span class="button" style="color: grey; cursor: not-allowed;" title="Experiment not finished yet.">Not Ready</span>')

    analysis_button.short_description = 'Analysis'
    
    def view_results_button(self, obj):
        # Use 'experiments:view_results' instead of 'admin:view_results'
        if obj.ready:
            url = reverse('experiments:view_results', args=[obj.id])
            return format_html('<a class="button" href="{}">View Results</a>', url)
        else:
            return format_html('<span class="button" style="color: grey; cursor: not-allowed;" title="Experiment not finished yet.">Not Ready</span>')

    view_results_button.short_description = 'Results'
    
    def participants_count(self, obj):
        # Calculate the number of participants based on treatment and control groups
        if obj.treatment_group.count() + obj.control_group.count() == 10000:
            return 'N/A'
        else:
            return obj.treatment_group.count() + obj.control_group.count()

    participants_count.short_description = '# participants'

    list_display = (
        'id', 'name', 'owner','participants_count', 'treatment_size',
        'segmentation_button', 'analysis_button', 'days_left', 'view_results_button',
    )


    list_display_links = ('id', 'name', 'owner', 'treatment_size')

    # list_filter = ('owner',)  # Add more fields for filtering as needed
    # search_fields = ('name', 'owner')  # Add more fields for searching as needed
    
@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['customer_uuid', 'first_action_month', 'location_title','cluster_name', 'rfm',
                    'rfm_title', 'timestamp_month', 'month_of_life', 'rides', 'revenue_excl_vat',
                    'clv']


    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv_admin),] 
        return new_urls + urls
    
    def upload_csv_admin(self, request): 
        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data[1:]:
                fields = x.split(",")

                if len(fields) >= 11:  # Adjust the index based on the number of columns in your CSV
                    try:
                        timestamp_str = fields[6].strip()  # Assuming 'TIMESTAMP_MONTH' is at index 6
                        timestamp_month = timezone.make_aware(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")).date()
                        first_action_month = timezone.make_aware(datetime.strptime(fields[1].strip(), "%Y-%m-%d %H:%M:%S.%f")).date()  # Assuming 'FIRST_ACTION_MONTH' is at index 1
                    except (IndexError, ValueError) as e:
                        print(f"Skipping line (unable to parse timestamp): {x}")
                        print(f"Error details: {e}")
                        continue

                    rides_value = float(fields[8].strip()) if fields[8].strip() else 0.0  # Assuming 'RIDES' is at index 8
                    revenue_excl_vat = Decimal(fields[9].strip()) if fields[9].strip() else Decimal(0.0)  # Assuming 'REVENUE_EXCL_VAT' is at index 9
                    cluster_name = fields[3].strip()  # Assuming 'CLUSTER_NAME' is at index 3
                    rfm = Decimal(fields[4].strip()) if fields[4].strip() else Decimal(0.0)
                    rfm_title = fields[5].strip()  # Assuming 'RFM_TITLE' is at index 5

                    # Create a new User instance for each row in the CSV
                    user_instance = User(
                        customer_uuid=fields[0].strip(),
                        location_title=fields[2].strip(),  # Assuming 'LOCATION_TITLE' is at index 2
                        first_action_month=first_action_month,
                        month_of_life=int(fields[7].strip()) if fields[7].strip() else 0,  # Assuming 'MONTH_OF_LIFE' is at index 7
                        timestamp_month=timestamp_month,
                        rides=rides_value,
                        revenue_excl_vat=revenue_excl_vat,
                        clv=Decimal(fields[10].strip()) if fields[10].strip() else Decimal(0.0),  # Assuming 'CLV' is at index 10
                        cluster_name=cluster_name,
                        rfm=rfm,
                        rfm_title=rfm_title,
                    )

                    # Save the instance to the database
                    user_instance.save()
                    print(f"User instance saved: {user_instance}")
                else:
                    print(f"Skipping line (insufficient fields): {x}")


                            
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)