from django.db import models
from django.utils import timezone
from datetime import timedelta

class Experiment(models.Model):
    CRITERIA_AND_FILTER_CHOICES = [('location','Location'), ('age', 'Age'), ('avg_minutes_per_ride', 'Minutes Per Ride')]
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.CharField(max_length=70)
    business_sponsor = models.CharField(max_length=70, blank=True)
    start_date = models.DateTimeField()
    duration_days = models.PositiveIntegerField()
    criteria_field = models.CharField(max_length=30, choices=CRITERIA_AND_FILTER_CHOICES, blank=True)
    criteria = models.CharField(max_length=255, blank=True)
    filter_field = models.CharField(max_length=30, choices=CRITERIA_AND_FILTER_CHOICES, blank=True)
    filter = models.CharField(max_length=255, blank=True)
    treatment_group_ratio = models.PositiveIntegerField(default=50, help_text='Percentage of users to receive treatment')
    treatment_group = models.ManyToManyField('User', related_name='treatment_group', blank=True)
    control_group = models.ManyToManyField('User', related_name='control_group', blank=True)

    def calculate_percentage(self):
        current_date = timezone.now()
        start_date = self.start_date
        end_date = start_date + timedelta(days=self.duration_days)

        if current_date < start_date:
            return 0
        elif current_date > end_date:
            return 100
        else:
            elapsed_days = (current_date - start_date).days
            percentage = (elapsed_days / self.duration_days) * 100
            return round(min(percentage, 100))
        
    def calculate_color(self):
        percentage = self.calculate_percentage()

        if percentage == 0:
            return 'yellow'
        elif percentage == 100:
            return 'grey'
        else:
            return 'green'
        
class User(models.Model):
    user_id = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    age = models.IntegerField()
    avg_minutes_per_ride = models.DecimalField(max_digits=10,decimal_places=3)
