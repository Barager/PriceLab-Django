# Generated by Django 5.0.1 on 2024-01-24 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0021_remove_experiment_csv_file_experiment_csv_file_path_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='csv_file',
            field=models.FileField(blank=True, null=True, upload_to='csv_files/'),
        ),
    ]
