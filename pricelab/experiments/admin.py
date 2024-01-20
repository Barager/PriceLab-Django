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


from .models import Experiment
from .models import User

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/calculate-groups/',
                self.admin_site.admin_view(self.calculate_groups),
                name='calculate-groups',
            ),
        ]
        return custom_urls + urls

    def calculate_groups(self, request, object_id):
        experiment = self.get_object(request, object_id)
        experiment.save()
        url = reverse('admin:experiments_experiment_change', args=[experiment.id])
        return redirect(url)

    def calculate_groups_button(self, obj):
        url = reverse('admin:calculate-groups', args=[obj.id])
        return format_html('<a class="button" href="{}">Segment Users</a>', url)

    calculate_groups_button.short_description = 'Calculate Groups'

    list_display = ('id', 'name', 'owner', 'treatment_group_ratio', 'calculate_groups_button')


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
    

