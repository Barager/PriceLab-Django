from django.db import models

class Experiment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.CharField(max_length=70)
    business_sponsor = models.CharField(max_length=70, blank=True)
    start_date = models.DateTimeField()
    duration_days = models.IntegerField()
    

