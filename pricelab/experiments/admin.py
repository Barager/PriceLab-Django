from django.contrib import admin

from .models import Experiment
from .models import User

@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'owner', 'business_sponsor', 'start_date', 'duration_days','criteria_field', 'criteria', 'filter_field', 'filter', 'treatment_group_ratio']

@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'location', 'age', 'avg_minutes_per_ride']