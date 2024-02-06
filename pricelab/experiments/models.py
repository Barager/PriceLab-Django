from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
import random
import pandas as pd
import numpy as np 
from django.db.models.fields.related import ManyToManyRel
import time


from sklearn.model_selection import StratifiedShuffleSplit

class Experiment(models.Model):
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.CharField(max_length=70)
    business_sponsor = models.CharField(max_length=70, blank=True)
    start_date = models.DateTimeField()
    duration_days = models.PositiveIntegerField()
    treatment_size = models.FloatField(default=0.5,help_text='Percentage of users to receive treatment',)
    treatment_group = models.ManyToManyField('User', related_name='treatment_group', blank=True)
    control_group = models.ManyToManyField('User', related_name='control_group', blank=True)
    ready = models.BooleanField(default=False, help_text='Experiment ready for analysis')
    selected_criteria = models.CharField(max_length=255, blank=True)
    selected_tests = models.ManyToManyField('Test', blank=True)
    published = models.BooleanField(default=False)
    
    @property
    def days_left(self):
        
        if self.treatment_group.all().count() == 0:
            end_date = self.start_date + timedelta(days=self.duration_days)
            return (end_date - self.start_date).days
        else:
            current_date = timezone.now()
            end_date = self.start_date + timedelta(days=self.duration_days)
            remaining_days = (end_date - current_date).days
            
            return max(remaining_days, 0)
    
    
    def changelist_view(self, request, extra_context=None):
        # Update readiness status for all experiments
        experiments = Experiment.objects.all()

        for experiment in experiments:
            experiment.ready_for_analysis()

        return super().changelist_view(request, extra_context=extra_context)
    
    def ready_for_analysis(self):
        current_date = timezone.now()
        end_date = self.start_date + timedelta(days=self.duration_days)

        if end_date < current_date:
            self.ready = True
        else:
            self.ready = False

        self.save()
        return self.ready
    
    
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
        
    # def filter_users(self):
    #     selected_segments = []

    #     # Collect selected segments from the form
    #     for field_name, _ in self.user_fields:
    #         if hasattr(self, field_name):
    #             selected_segments.append((field_name, getattr(self, field_name)))

    #     # Filter users based on selected segments
    #     filtered_users = User.objects.all()
    #     for field_name, values in selected_segments:
    #         if field_name == 'location_title':
    #             filtered_users = filtered_users.filter(**{f"{field_name}__in": values})
    #         elif field_name in ['rfm_title', 'cluster_name']:
    #             filtered_users = filtered_users.filter(**{f"{field_name}__in": values})
    #         else:
    #             # Handle other field types as needed
    #             pass

    #     return filtered_users

    # def save(self, *args, **kwargs):
    #     # Set user_fields attribute based on the form logic
    #     self.user_fields = [
    #         (field.name, field.verbose_name)
    #         for field in User._meta.get_fields()
    #         if hasattr(field, 'verbose_name') and field.name != 'id' and not isinstance(field, ManyToManyRel)
    #     ]

    #     super().save(*args, **kwargs)

    #     # Filter users based on selected segments
    #     filtered_users = self.filter_users()

    #     # users = User.objects.all()
    #     user_ids = [user.id for user in filtered_users]
    #     random.shuffle(user_ids)
    #     num_users = len(user_ids)

    #     # Calculate the number of users for treatment and control groups
    #     num_treatment_group = int(num_users * self.treatment_size)
    #     num_control_group = num_users - num_treatment_group

    #     # Assign users to treatment and control groups
    #     self.treatment_group.set(filtered_users[:num_treatment_group])
    #     self.control_group.set(filtered_users[num_treatment_group:])
    #     print(f'Number of users in treatment group: {num_treatment_group}\nNumber of users in control group: {num_control_group}\nOut of {len(User.objects.all())} users')
    #     print('==========================')

    
class User(models.Model):
    customer_uuid = models.CharField(max_length=255)
    location_title = models.CharField(max_length=255)
    first_action_month = models.DateField(default=datetime(2015, 7, 2))
    timestamp_month = models.DateField(default=datetime(2015, 7, 2))
    month_of_life = models.IntegerField(default=0)
    rfm = models.FloatField(default=0.0)  
    rfm_title = models.CharField(default='',max_length=255)
    rides = models.FloatField(default=0)  
    cluster_name = models.CharField(default='', max_length=255)
    revenue_excl_vat = models.FloatField(default=0.0) 
    clv = models.FloatField(default=0.0)
    
    
class Test(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    # Add any additional fields needed for your specific tests

    def __str__(self):
        return self.name