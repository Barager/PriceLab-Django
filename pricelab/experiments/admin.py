from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Experiment
from .models import User

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'owner', 'business_sponsor', 'start_date', 'duration_days','criteria_field', 'criteria', 'filter_field', 'filter', 'treatment_group_ratio']

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
    


