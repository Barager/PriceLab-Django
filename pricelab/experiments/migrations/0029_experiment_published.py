# Generated by Django 5.0.1 on 2024-01-31 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0028_remove_experiment_criteria_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]
