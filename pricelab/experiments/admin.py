from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django import forms

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
        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
    


