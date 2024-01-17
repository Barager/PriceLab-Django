from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

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
    list_display = ['user_id', 'location', 'age', 'avg_minutes_per_ride']

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls
    
    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request,'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)
            

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = User.objects.update_or_create(
                    user_id = fields[0],
                    location = fields[1],
                    age = fields[2],
                    avg_minutes_per_ride = fields[3],
                )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
    


