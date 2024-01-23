from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from datetime import datetime
import pandas as pd

from scipy.stats import ttest_ind, shapiro, levene, mannwhitneyu



from .models import Experiment
from .models import User

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        
        
    # def upload_csv(self, request):
    #     if request.method == "POST":
    #         csv_file = request.FILES["csv_upload"]

    #         if not csv_file.name.endswith('.csv'):
    #             messages.warning(request, 'The wrong file type was uploaded')
    #             return HttpResponseRedirect(request.path_info)

    #         # Read CSV data into Pandas DataFrame
    #         try:
    #             df = pd.read_csv(csv_file)
    #         except pd.errors.EmptyDataError:
    #             messages.warning(request, 'The CSV file is empty')
    #             return HttpResponseRedirect(request.path_info)
    #         except pd.errors.ParserError:
    #             messages.warning(request, 'Error parsing the CSV file')
    #             return HttpResponseRedirect(request.path_info)
        
        
    def perform_test(self, request, object_id):
        experiment = self.get_object(request, object_id)
        
        if experiment.ready:
            treatment_group = experiment.treatment_group.all()
            control_group = experiment.control_group.all()

            # Extract the relevant data for the t-test (modify this based on your actual data structure)
            treatment_data = [user.revenue_excl_vat for user in treatment_group]
            control_data = [user.revenue_excl_vat for user in control_group]

            # Shapiro-Wilk test for normality
            _, p_value_treatment = shapiro(treatment_data)
            _, p_value_control = shapiro(control_data)

            # Levene's test for homogeneity of variances
            _, p_value_levene = levene(treatment_data, control_data)

            alternative_test_performed = False

            if p_value_treatment > 0.05 and p_value_control > 0.05 and p_value_levene > 0.05:
                # Perform t-test assuming unequal variances
                t_statistic, p_value = ttest_ind(treatment_data, control_data, equal_var=False)

                # Save the results in a variable (modify this based on your requirements)
                experiment.t_test_result = {'test': 't-test', 't_statistic': t_statistic, 'p_value': p_value}
                experiment.save()

                messages.success(request, 'T-test performed successfully.')
            else:
                alternative_test_performed = True

                # Check for alternative tests (e.g., Mann-Whitney U test for non-parametric data)
                if p_value_treatment <= 0.05 or p_value_control <= 0.05:
                    # Perform Mann-Whitney U test as an alternative
                    _, mannwhitney_p_value = mannwhitneyu(treatment_data, control_data)
                    experiment.t_test_result = {'test': 'Mann-Whitney U test', 'p_value': mannwhitney_p_value}
                    messages.warning(request, 'Assumptions for t-test not met. Performed Mann-Whitney U test.')
                else:
                    # If neither t-test nor Mann-Whitney U test is appropriate, add more alternative tests as needed
                    experiment.t_test_result = {'test': 'Alternative test', 'message': 'Additional alternative test needed.'}
                    messages.warning(request, 'Assumptions for t-test not met. Additional alternative test needed.')

            if alternative_test_performed:
                print(f'Test results: {experiment.t_test_result}')

        elif not experiment.uploaded:
            messages.warning(request, 'Data files not uploaded yet.')
        else:
            messages.warning(request, 'Experiment not done yet.')

        url = reverse('admin:experiments_experiment_changelist')#, args=[experiment.id])
        return redirect(url)

    def test_button(self, obj):
        url = reverse('admin:perform-test', args=[obj.id])
        return format_html('<a class="button" href="{}">Perform Test</a>', url)

    test_button.short_description = 'Test'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/assign-treatment/',
                self.admin_site.admin_view(self.assign_treatment),
                name='assign-treatment',
            ),
            path(
                '<path:object_id>/perform-test/',
                self.admin_site.admin_view(self.perform_test),
                name='perform-test',
            ),
        ]
        return custom_urls + urls

    def assign_treatment(self, request, object_id):
        experiment = self.get_object(request, object_id)
        experiment.save()
        url = reverse('admin:experiments_experiment_change', args=[experiment.id])
        return redirect(url)

    def assign_treatment_button(self, obj):
        url = reverse('admin:assign-treatment', args=[obj.id])
        return format_html('<a class="button" href="{}">Assign</a>', url)

    assign_treatment_button.short_description = 'Assign treatment(s)'

    list_display = (
        'id', 'name', 'owner', 'treatment_size', 'ready', 'assign_treatment_button', 'test_button'
    )
    list_display_links = ('id', 'name', 'owner', 'treatment_size')
    
    
    
@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['customer_uuid', 'location_title', 'timestamp_month', 'rides', 'revenue_excl_vat']

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls
    
    def upload_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data[1:]:
                fields = x.split(",")

                if len(fields) >= 3:  # Ensure fields has at least 3 elements
                    try:
                        timestamp_month = timezone.make_aware(datetime.strptime(fields[2], "%Y-%m-%d"))
                    except (IndexError, ValueError):
                        print(f"Skipping line: {x}. Unable to parse timestamp.")
                        continue

                    rides_value = float(fields[3]) if len(fields) > 3 and fields[3] else 0.0

                    if len(fields) >= 5:
                        revenue_excl_vat = fields[4]
                    else:
                        revenue_excl_vat = 0.0

                    created = User.objects.update_or_create(
                        customer_uuid=fields[0],
                        location_title=fields[1],
                        timestamp_month=timestamp_month,
                        rides=rides_value,
                        revenue_excl_vat=revenue_excl_vat
                    )
                else:
                    # Handle the case where the fields list doesn't have enough elements
                    print(f"Skipping line: {x}. Insufficient fields.")

                            
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
    

