# Generated by Django 5.0.1 on 2024-01-24 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0016_user_clv_user_first_action_month_user_month_of_life'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='clv',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='user',
            name='revenue_excl_vat',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='user',
            name='rfm',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='user',
            name='rides',
            field=models.FloatField(),
        ),
    ]
