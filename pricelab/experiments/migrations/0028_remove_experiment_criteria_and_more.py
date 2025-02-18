# Generated by Django 5.0.1 on 2024-01-30 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0027_test_remove_experiment_csv_file_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experiment',
            name='criteria',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='criteria_field',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='filter',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='filter_field',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='ready_2',
        ),
        migrations.AddField(
            model_name='experiment',
            name='selected_criteria',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
