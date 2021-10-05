# Generated by Django 3.2.4 on 2021-09-28 08:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PayloadThreshold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload_description', models.CharField(max_length=255)),
                ('payload_code', models.CharField(max_length=255)),
                ('percentage_threshold', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
            options={
                'db_table': 'PayloadThreshold',
            },
        ),
        migrations.CreateModel(
            name='PayloadUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time_uploaded', models.DateTimeField(auto_now=True)),
                ('message_type', models.CharField(choices=[('SVCREC', 'SVCREC'), ('DDC', 'DDC'), ('DDCOUT', 'DDCOUT'), ('REV', 'REV'), ('BEDOCC', 'BEDOCC')], max_length=100)),
                ('file', models.FileField(blank=True, null=True, upload_to='uploads')),
            ],
            options={
                'db_table': 'PayloadUploads',
            },
        ),
        migrations.CreateModel(
            name='TransactionSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_date_time', models.DateTimeField(auto_now=True)),
                ('message_type', models.CharField(choices=[('SVCREC', 'SVCREC'), ('DDC', 'DDC'), ('DDCOUT', 'DDCOUT'), ('REV', 'REV'), ('BEDOCC', 'BEDOCC')], max_length=100)),
                ('org_name', models.CharField(max_length=255)),
                ('facility_hfr_code', models.CharField(max_length=255)),
                ('total_passed', models.IntegerField(default=0)),
                ('total_failed', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Transactions summary',
                'db_table': 'TransactionSummary',
            },
        ),
        migrations.CreateModel(
            name='ValidationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('rule_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'ValidationRules',
            },
        ),
        migrations.CreateModel(
            name='TransactionSummaryLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payload_object', models.TextField()),
                ('transaction_status', models.BooleanField(default=0)),
                ('error_message', models.TextField()),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='ValidationManagement.transactionsummary')),
            ],
            options={
                'verbose_name_plural': 'Transactions summary lines',
                'db_table': 'TransactionSummaryLine',
            },
        ),
        migrations.CreateModel(
            name='FieldValidationMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_type', models.CharField(choices=[('SVCREC', 'SVCREC'), ('DDC', 'DDC'), ('DDCOUT', 'DDCOUT'), ('REV', 'REV'), ('BEDOCC', 'BEDOCC')], max_length=100)),
                ('field', models.CharField(max_length=255)),
                ('validation_rule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='ValidationManagement.validationrule')),
            ],
            options={
                'db_table': 'FieldValidationMappings',
            },
        ),
    ]