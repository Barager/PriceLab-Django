from django.contrib import admin

from .models import Experiment

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'owner', 'business_sponsor', 'start_date', 'duration_days']
