import csv
import json
from celery import Celery, shared_task
from API import validators as validators
from Core import models as core_models
from MasterData import models as master_data_models
import os
from django.http import HttpResponse
from datetime import datetime, timedelta
from pathlib import Path
from Core import views as core_views
from ValidationManagement import models as validation_management_models
from TerminologyServicesManagement import models as terminology_management_services_models
from functools import wraps
from django.db.models import Count
import logging
from django.conf import settings


#SETTING UP LOGGING
fmt = getattr(settings, 'LOG_FORMAT', None)
lvl = getattr(settings, 'LOG_LEVEL', logging.DEBUG)

logging.basicConfig(format=fmt, level=lvl)


app = Celery()

def skip_if_running(f):
    task_name = '{f.__module__}.{f.__name__}'

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        workers = self.app.control.inspect().active()

        for worker, tasks in workers.items():
            for task in tasks:
                if (task_name == task['name'] and
                            tuple(args) == tuple(task['args']) and
                            kwargs == task['kwargs'] and
                            self.request.id != task['id']):
                    logging.debug('task {task_name} ({args}, {kwargs}) is running on {worker}, skipping')

                    return None

        return f(self, *args, **kwargs)

    return wrapped


#This function checks for uploaded csv files in the uploads
# directory in the server and picks them up for processing
@app.task()
def save_payload_from_csv():
    root_path = "uploads"
    i = 0
    for subdir, _, _ in os.walk(root_path):
        for file in os.listdir(subdir):
            file_path = os.path.join(root_path, file) # This will join the paths to create one path intelligently
            logging.debug(file_path)
            with open(file_path, 'r') as fp:
                lines = csv.reader(fp, delimiter=',')

                imported_payload = core_views.regenerate_json_payload_from_csv(lines)
                logging.debug(imported_payload)

                result = validators.validate_received_payload(json.loads(imported_payload))
                transaction_status = result["transaction_status"]
                transaction_id = result["transaction_id"]

                os.remove(file_path)

                if transaction_status is False:
                    logging.debug("validation failed")
                else:
                    logging.debug("validation successful")
                    json_imported_payload = json.loads(imported_payload)
                    message_type = json_imported_payload["messageType"]
                    facility_name = json_imported_payload["orgName"]
                    facility_hfr_code = json_imported_payload["facilityHfrCode"]

                    items = json_imported_payload["items"]

                    # Service received parents lines
                    if message_type == "SVCREC":
                        instance_service_received = core_models.ServiceReceived()
                        instance_service_received.transaction_id = transaction_id
                        instance_service_received.org_name = facility_name
                        instance_service_received.facility_hfr_code = facility_hfr_code
                        instance_service_received.save()

                        for item in items:
                            instance_service_received_items = core_models.ServiceReceivedItems()
                            instance_service_received_items.service_received_id = instance_service_received.id
                            instance_service_received_items.department_name = item["deptName"]
                            instance_service_received_items.department_id = item["deptId"]
                            instance_service_received_items.patient_id = item["patId"]
                            instance_service_received_items.gender = item["gender"]
                            instance_service_received_items.date_of_birth = validators.convert_date_formats(item["dob"])
                            instance_service_received_items.med_svc_code = item["medSvcCode"]
                            instance_service_received_items.confirmed_diagnosis = item["confirmedDiagnosis"]
                            instance_service_received_items.differential_diagnosis = item["differentialDiagnosis"]
                            instance_service_received_items.provisional_diagnosis = item["provisionalDiagnosis"]
                            instance_service_received_items.service_date = validators.convert_date_formats(item["serviceDate"])
                            instance_service_received_items.service_provider_ranking_id = item["serviceProviderRankingId"]
                            instance_service_received_items.visit_type = item["visitType"]
                            instance_service_received_items.save()

                    # Death in Facility
                    if message_type == "DDC":
                        instance_death_by_disease_case_at_facility = core_models.DeathByDiseaseCaseAtFacility()
                        instance_death_by_disease_case_at_facility.transaction_id = transaction_id
                        instance_death_by_disease_case_at_facility.org_name = facility_name
                        instance_death_by_disease_case_at_facility.facility_hfr_code = facility_hfr_code
                        instance_death_by_disease_case_at_facility.save()

                        for item in items:
                            instance_death_by_disease_case_items = core_models.DeathByDiseaseCaseAtFacilityItems()
                            instance_death_by_disease_case_items.death_by_disease_case_at_facility_id = instance_death_by_disease_case_at_facility.id
                            instance_death_by_disease_case_items.ward_id = item["wardId"]
                            instance_death_by_disease_case_items.ward_name = item["wardName"]
                            instance_death_by_disease_case_items.patient_id = item["patId"]
                            instance_death_by_disease_case_items.first_name = item["firstName"]
                            instance_death_by_disease_case_items.middle_name = item["middleName"]
                            instance_death_by_disease_case_items.last_name = item["lastName"]
                            instance_death_by_disease_case_items.gender = item["gender"]
                            instance_death_by_disease_case_items.date_of_birth = validators.convert_date_formats(item["dob"])
                            instance_death_by_disease_case_items.cause_of_death = item["causeOfDeath"]
                            instance_death_by_disease_case_items.immediate_cause_of_death = item["immediateCauseOfDeath"]
                            instance_death_by_disease_case_items.underlying_cause_of_death = item["underlyingCauseOfDeath"]
                            instance_death_by_disease_case_items.date_death_occurred = validators.convert_date_formats(item["dateDeathOccurred"])
                            instance_death_by_disease_case_items.save()

                            # Death by Disease Case Out of Faciity lines

                    # Death outside at Facility
                    if message_type == "DDCOUT":
                        instance_death_by_disease_case_not_at_facility = core_models.DeathByDiseaseCaseNotAtFacility()
                        instance_death_by_disease_case_not_at_facility.transaction_id = transaction_id
                        instance_death_by_disease_case_not_at_facility.org_name = facility_name
                        instance_death_by_disease_case_not_at_facility.facility_hfr_code = facility_hfr_code
                        instance_death_by_disease_case_not_at_facility.save()

                        for item in items:
                            instance_death_by_disease_case_items_not_at_facility = core_models.DeathByDiseaseCaseNotAtFacilityItems()
                            instance_death_by_disease_case_items_not_at_facility.death_by_disease_case_not_at_facility_id = instance_death_by_disease_case_not_at_facility.id
                            instance_death_by_disease_case_items_not_at_facility.place_of_death_id = item["placeOfDeathId"]
                            instance_death_by_disease_case_items_not_at_facility.gender = item["gender"]
                            instance_death_by_disease_case_items_not_at_facility.date_of_birth = validators.convert_date_formats(item["dob"])
                            instance_death_by_disease_case_items.cause_of_death = item["causeOfDeath"]
                            instance_death_by_disease_case_items.immediate_cause_of_death = item[
                                "immediateCauseOfDeath"]
                            instance_death_by_disease_case_items.underlying_cause_of_death = item[
                                "underlyingCauseOfDeath"]
                            instance_death_by_disease_case_items_not_at_facility.date_death_occurred = validators.convert_date_formats(item["dateDeathOccurred"])
                            instance_death_by_disease_case_items_not_at_facility.death_id = item["deathId"]
                            instance_death_by_disease_case_items_not_at_facility.save()

                            # Bed Occupany parent lines

                    # Bed Occupancy
                    if message_type == "BEDOCC":
                        instance_bed_occupancy = core_models.BedOccupancy()
                        instance_bed_occupancy.transaction_id = transaction_id
                        instance_bed_occupancy.org_name = facility_name
                        instance_bed_occupancy.facility_hfr_code = facility_hfr_code
                        instance_bed_occupancy.save()

                        for item in items:
                            instance_bed_occupancy_items = core_models.BedOccupancyItems()

                            instance_bed_occupancy_items.bed_occupancy_id = instance_bed_occupancy.id
                            instance_bed_occupancy_items.ward_id = item["wardId"]
                            instance_bed_occupancy_items.ward_name = item["wardName"]
                            instance_bed_occupancy_items.patient_id = item["patId"]
                            instance_bed_occupancy_items.admission_date = validators.convert_date_formats(item["admissionDate"])
                            instance_bed_occupancy_items.discharge_date = validators.convert_date_formats(item["dischargeDate"])
                            instance_bed_occupancy_items.save()

                    # Revenue
                    if message_type == "REV":
                        instance_revenue_received = core_models.RevenueReceived()
                        instance_revenue_received.transaction_id = transaction_id
                        instance_revenue_received.org_name = facility_name
                        instance_revenue_received.facility_hfr_code = facility_hfr_code
                        instance_revenue_received.save()

                        for item in items:
                            instance_revenue_received_items = core_models.RevenueReceivedItems()
                            instance_revenue_received_items.revenue_received_id = instance_revenue_received.id
                            instance_revenue_received_items.system_trans_id = item["systemTransId"]
                            instance_revenue_received_items.transaction_date = validators.convert_date_formats(item["transactionDate"])
                            instance_revenue_received_items.patient_id = item["patId"]
                            instance_revenue_received_items.gender = item["gender"]
                            instance_revenue_received_items.date_of_birth = validators.convert_date_formats(item["dob"])
                            instance_revenue_received_items.med_svc_code = item["medSvcCode"]
                            instance_revenue_received_items.payer_id = item["payerId"]
                            instance_revenue_received_items.exemption_category_id = item["exemptionCategoryId"]
                            instance_revenue_received_items.billed_amount = item["billedAmount"]
                            instance_revenue_received_items.waived_amount = item["waivedAmount"]
                            instance_revenue_received_items.service_provider_ranking_id = item["serviceProviderRankingId"]
                            instance_revenue_received_items.save()


#The function will update the records passed and failed as the
# payload is being processed.
def update_transaction_summary(transaction_id):
    transaction = validation_management_models.TransactionSummary.objects.get(id=transaction_id)
    transaction.total_passed += 1
    transaction.total_failed -= 1
    transaction.save()


#The function will process bed occupancy data received from emrs
# and will calculate the BOR(Bed Occupancy rate) per facility and
# per patient on a daily basis
#breaking it down to patient level will elimitate the issue with
# discharging of patients at the facility
@app.task()
def calculate_and_save_bed_occupancy_rate():
    discharge_date = datetime.now().strftime("%Y-%m-%d")

    # Get all active bed occupancy transactions
    bed_occupancies = core_models.BedOccupancy.objects.filter(transaction__is_active=True,
                                                           is_processed=False).order_by('-id')[:5]

    # Loop through each transaction
    for bed_occupancy in bed_occupancies:
        facility_hfr_code = bed_occupancy.facility_hfr_code

        # Get the bed occupancy items associated with each transaction
        bed_occupancy_items = core_models.BedOccupancyItems.objects.filter(bed_occupancy__transaction__is_active=True,
                                                                           bed_occupancy_id=bed_occupancy.id)
        if bed_occupancy_items is not None:
            # Lopp through each bed occupancy item
            for item in bed_occupancy_items:
                # Get ward details for each record in the bed occupancy items
                ward = master_data_models.Ward.objects.filter(local_ward_id=item.ward_id,
                                                                       facility__facility_hfr_code=facility_hfr_code).first()
                if ward is not None:
                    # Get Patient admission period to add days to it
                    instance_patient = core_models.BedOccupancyReport.objects.filter(patient_id=item.patient_id,
                                                                                     admission_date=item.admission_date)
                    if instance_patient.count() == 0:
                        get_patient_admission_discharge_period = core_models.BedOccupancyItems.objects.filter(
                            patient_id=item.patient_id, admission_date=item.admission_date,
                            discharge_date=item.discharge_date, bed_occupancy__transaction__is_active=True).first()

                        # Patient has does not have both admission and discharge dates
                        if get_patient_admission_discharge_period is None:
                            get_patient_admission_period = core_models.BedOccupancyItems.objects.filter(
                                patient_id=item.patient_id,
                                admission_date=item.admission_date, bed_occupancy__transaction__is_active=True
                            ).first()
                            # Patient has admission date only
                            if get_patient_admission_period is not None:
                                discharge_date = bed_occupancy_items.last().admission_date
                            else:
                                get_patient_discharge_period = core_models.BedOccupancyItems.objects.filter(
                                    patient_id=item.patient_id,
                                    discharge_date=item.discharge_date, bed_occupancy__transaction__is_active=True).first()
                                # Patient has discharge date only
                                if get_patient_discharge_period is not None:
                                    discharge_date = get_patient_discharge_period.discharge_date
                        # Patient has both admission and discharge dates
                        else:
                            # admission_date = get_patient_admission_discharge_period.admission_date
                            discharge_date = get_patient_admission_discharge_period.discharge_date
                    else:
                        pass
                    try:
                        bed_occupancy_rate = 1 / int(ward.number_of_beds) * 100

                        create_bed_occupancy_report_record(discharge_date,item, bed_occupancy_rate,
                                                           facility_hfr_code)

                    except Exception as e:
                        logging.debug(e)

        bed_occupancy = core_models.BedOccupancy.objects.get(id=bed_occupancy.id)
        bed_occupancy.is_processed = True
        bed_occupancy.save()


#This function will be run periodically to find any duplicates in the
# uploaded csv and deactivate transactions taht are detected as duplicates
@app.task()
def cleanup_uploaded_csv_files(request):
    today = datetime.now().date()
    formatted_today = str(today) + " 00:00:00"
    discovered_duplicate_transactions = validation_management_models.TransactionSummary.objects.\
                                                filter(transaction_date_time__gte = formatted_today, is_active=True).values('message_type',
                                                                                           'facility_hfr_code',
                                                                                           'total_passed',
                                                                                           'total_failed') \
        .annotate(records=Count('message_type')) \
        .filter(records__gt=1)

    for transaction in discovered_duplicate_transactions:
        facility = master_data_models.Facility.objects.filter(facility_hfr_code = transaction['facility_hfr_code']).first()

        # Check if facility sends CSVs as mapping will be done on the the HDRAdmin
        if facility.uses_cpt_internally is False:
            facility_transactions_all = validation_management_models.TransactionSummary.objects.filter(
                message_type=transaction['message_type'],
                transaction_date_time__gte=formatted_today,
                facility_hfr_code=transaction['facility_hfr_code'],
                total_passed=transaction['total_passed'],
                total_failed=transaction['total_failed'], is_active=True).order_by('id')

            print(facility_transactions_all.count())

            facility_transactions = validation_management_models.TransactionSummary.objects.filter(
                                                            message_type=transaction['message_type'],
                                                            transaction_date_time__gte=formatted_today,
                                                             facility_hfr_code=transaction['facility_hfr_code'],
                                                            total_passed=transaction['total_passed'],
                                                            total_failed=transaction['total_failed'], is_active=True).order_by('id')[1:]
            print(facility_transactions.count())

            for facility_transaction in facility_transactions:
                facility_transaction.is_active = False
                facility_transaction.save()


#This function will save the individual patient records calculated
# for the bed occupancy and save them as daily records
def create_bed_occupancy_report_record(discharge_date, item, bed_occupancy_rate, facility_hfr_code):
    for x in range(int((discharge_date - item.admission_date).days)):
        instance_bed_occupancy_report = core_models.BedOccupancyReport()
        instance_bed_occupancy_report.patient_id = item.patient_id
        instance_bed_occupancy_report.date = item.admission_date + timedelta(days=x)
        instance_bed_occupancy_report.admission_date = item.admission_date
        instance_bed_occupancy_report.ward_id = item.ward_id
        instance_bed_occupancy_report.ward_name = item.ward_name
        instance_bed_occupancy_report.bed_occupancy = bed_occupancy_rate
        instance_bed_occupancy_report.facility_hfr_code = facility_hfr_code
        instance_bed_occupancy_report.save()

#This function will import all the icd10 codes from the json resource in the repo
def import_icd_10_codes():
    with open ('icd10codes.json',"r") as f: # Import the CDC codes from the json file in the repo
        data = json.load(f)

    #the ICD10 structure is in four levels and has to be entered the same way
    for x in data:
        categories = x['category']
        sub_categories = x['subCategories']
        identifier = categories.split('(', 1)[1].split(')')[0]

        category = terminology_management_services_models.ICD10CodeCategory.objects.filter(identifier=identifier).first()

        if category is None:
            # # insert category
            instance_category = terminology_management_services_models.ICD10CodeCategory()
            instance_category.identifier = identifier
            instance_category.description = categories
            instance_category.save()
        else:
            pass
            logging.debug(categories)

        for sub_category in sub_categories:
            sub_category_name = sub_category['subCategoryName']
            sub_sub_categories = sub_category['subSubCategories']
            identifier = sub_category_name.split('(', 1)[1].split(')')[0]

            sub_category = terminology_management_services_models.ICD10CodeSubCategory.objects.filter(identifier=identifier).first()

            if sub_category is None:
                # # insert sub category
                instance_sub_category = terminology_management_services_models.ICD10CodeSubCategory()

                last_category = terminology_management_services_models.ICD10CodeCategory.objects.all().last()
                instance_sub_category.identifier = identifier
                instance_sub_category.description = sub_category_name
                instance_sub_category.category_id = last_category.id
                instance_sub_category.save()
            else:
                pass
                logging.debug(sub_category_name)

            # loop through the sub sub categories
            for sub_sub_category in sub_sub_categories:
                icd_10 = sub_sub_category["subSubCategoryName"]
                icd_10_code = sub_sub_category["subSubCategoryCode"]
                icd_sub_code_array = sub_sub_category["icd10Codes"]

                code = terminology_management_services_models.ICD10Code.objects.filter(code = icd_10_code).first()

                if code is None:
                    # # insert icd code
                    instance_icd_code = terminology_management_services_models.ICD10Code()

                    last_sub_category = terminology_management_services_models.ICD10CodeSubCategory.objects.all().last()
                    instance_icd_code.sub_category_id =  last_sub_category.id
                    instance_icd_code.code = icd_10_code
                    instance_icd_code.description = icd_10
                    instance_icd_code.save()
                else:
                    pass

                for y in icd_sub_code_array:
                    icd_10_sub_code = y["icd10Code"]
                    icd_10_sub_description = y["icd10Name"]

                    sub_code = terminology_management_services_models.ICD10SubCode.objects.filter(sub_code=icd_10_sub_code).first()

                    if sub_code is None:
                        # insert icd sub code
                        instance_icd_sub_code = terminology_management_services_models.ICD10SubCode()

                        last_code = terminology_management_services_models.ICD10Code.objects.all().last()
                        instance_icd_sub_code.code_id = last_code.id
                        instance_icd_sub_code.sub_code = icd_10_sub_code
                        instance_icd_sub_code.description = icd_10_sub_description
                        instance_icd_sub_code.save()
                    else:
                        pass


#This function will import all teh cpt codes from the json resource in the repo
def import_cpt_codes():
    with open('cpt.csv', 'r') as fp:
        lines = csv.reader(fp, delimiter=',')

        for line in lines:
            code = line[0]
            description = line[1]

            if code == "CATEGORY":
                category = terminology_management_services_models.CPTCodeCategory.objects.filter(description=description).first()

                if category is None:
                    instance_category = terminology_management_services_models.CPTCodeCategory()
                    instance_category.description = description
                    instance_category.save()

            elif code == "SUBCATEGORY":
                sub_category = terminology_management_services_models.CPTCodeSubCategory.objects.filter(description=description).first()

                if sub_category is None:
                    instance_sub_category = terminology_management_services_models.CPTCodeSubCategory()

                    last_category = terminology_management_services_models.CPTCodeCategory.objects.all().last()
                    instance_sub_category.category_id = last_category.id
                    instance_sub_category.description = description
                    instance_sub_category.save()
            else:
                codes = terminology_management_services_models.CPTCode.objects.filter(code=code).first()

                if codes is None:
                    instance_code = terminology_management_services_models.CPTCode()

                    last_sub_category = terminology_management_services_models.CPTCodeSubCategory.objects.all().last()
                    instance_code.sub_category_id = last_sub_category.id
                    instance_code.code = code
                    instance_code.description = description
                    instance_code.save()


