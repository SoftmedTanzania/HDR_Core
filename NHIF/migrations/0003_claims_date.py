# Generated by Django 3.2.4 on 2021-11-03 12:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('NHIF', '0002_alter_claims_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='claims',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
