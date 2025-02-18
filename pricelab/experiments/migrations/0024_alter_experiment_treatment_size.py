# Generated by Django 5.0.1 on 2024-01-25 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0023_alter_experiment_treatment_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='treatment_size',
            field=models.FloatField(default=0.5, help_text='Percentage of users to receive treatment'),
        ),
    ]
