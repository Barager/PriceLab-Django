from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import random
import pandas as pd
import numpy as np  

from sklearn.model_selection import StratifiedShuffleSplit

class Experiment(models.Model):
    CRITERIA_AND_FILTER_CHOICES = [('location_title','Location'), ('revenue_excl_vat', 'Revenue'), ('rides', 'Minutes Per Ride')]
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
    treatment_size = models.FloatField(default=.5, help_text='Percentage of users to receive treatment')
    treatment_group = models.ManyToManyField('User', related_name='treatment_group', blank=True)
    control_group = models.ManyToManyField('User', related_name='control_group', blank=True)
    ready = models.BooleanField(default=False, help_text='Experiment ready for analysis')
    uploaded = models.BooleanField(default=False, help_text='CSV uploaded')
    
    def ready_for_analysis(self):
        if self.start_date + timedelta(days=self.duration_days) < timezone.now() & self.uploaded:
            self.ready = True
        else:
            self.ready = False
        return
    
    
        

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
            return 'green'
        else:
            return 'grey' 
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        treatment_size = self.treatment_size
        criteria_field = self.criteria_field
        criteria = self.criteria
        
        # Ensure that criteria_field and criteria are not empty
        if criteria_field and criteria:
            users = User.objects.filter(**{criteria_field: criteria})
            user_ids = [user.id for user in users]
            random.shuffle(user_ids)
            num_users = len(user_ids)
            num_treatment_group = int(num_users * treatment_size / 100)
            self.treatment_group.set(user_ids[:num_treatment_group])
            self.control_group.set(user_ids[num_treatment_group:])
            treatment_size = self.treatment_size

            users = User.objects.values('id', 'location_title', 'rides')
            df = pd.DataFrame(users)

            sss = StratifiedShuffleSplit(n_splits=1, test_size=(1 - treatment_size), random_state=42)

            for train_idx, test_idx in sss.split(df, df[['location_title']]):
                
                treatment_ids = df.loc[train_idx, 'id'].tolist()
                control_ids = df.loc[test_idx, 'id'].tolist()
                self.treatment_group.set(treatment_ids)
                self.control_group.set(control_ids)
    
    
class User(models.Model):
    customer_uuid = models.CharField(max_length=255)
    location_title = models.CharField(max_length=255)
    timestamp_month = models.DateTimeField(default=datetime(2015, 7, 2))
    rides = models.FloatField(max_length=255)
    revenue_excl_vat = models.FloatField(max_length=255)
    