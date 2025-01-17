# Generated by Django 3.2 on 2023-07-25 20:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MasterData', '0005_rename_is_cpt_mapped_facility_uses_cpt_internally'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='department',
            options={'verbose_name_plural': '7. Departments'},
        ),
        migrations.AlterModelOptions(
            name='districtcouncil',
            options={'verbose_name_plural': '3. District Councils'},
        ),
        migrations.AlterModelOptions(
            name='exemption',
            options={'verbose_name_plural': '6. Exemptions'},
        ),
        migrations.AlterModelOptions(
            name='facility',
            options={'verbose_name_plural': '4. Facilities'},
        ),
        migrations.AlterModelOptions(
            name='gender',
            options={'verbose_name_plural': '9. Gender'},
        ),
        migrations.AlterModelOptions(
            name='payer',
            options={'verbose_name_plural': '5. Payers'},
        ),
        migrations.AlterModelOptions(
            name='placeofdeath',
            options={'verbose_name_plural': '11. Places Of Death'},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'verbose_name_plural': '2. Regions'},
        ),
        migrations.AlterModelOptions(
            name='serviceproviderranking',
            options={'verbose_name_plural': '10. Service Provider Rankings'},
        ),
        migrations.AlterModelOptions(
            name='ward',
            options={'verbose_name_plural': '8. Wards'},
        ),
        migrations.AlterModelOptions(
            name='zone',
            options={'verbose_name_plural': '1. Zones'},
        ),
    ]
