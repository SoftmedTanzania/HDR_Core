# Generated by Django 3.2.4 on 2021-11-26 11:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ValidationManagement', '0005_alter_payloadfieldmapping_message_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldvalidationmapping',
            name='new_message_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, to='ValidationManagement.payloadfieldmapping'),
            preserve_default=False,
        ),
    ]