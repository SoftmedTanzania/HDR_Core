from datetime import datetime, date
from dateutil.parser import parse
from ValidationManagement.models import FieldValidationMapping, ValidationRule, TransactionSummary, TransactionSummaryLine, PayloadThreshold
import json
import pytz
from MasterData import models as master_data_models
import logging
from django.conf import settings


#SETTING UP LOGGING
fmt = getattr(settings, 'LOG_FORMAT', None)
lvl = getattr(settings, 'LOG_LEVEL', logging.DEBUG)

logging.basicConfig(format=fmt, level=lvl)


#The function will run a check to see if the date is not a future date
def check_if_not_future_date(date):
    formatted_date = convert_date_formats(date)
    now = datetime.now().date()

    if formatted_date > now:
        return False
    else:
        return True


#The function will check that the given date is not a past date.
def check_if_not_past_date(date):
    formatted_date = convert_date_formats(date)
    now = datetime.now().date()

    if formatted_date < now:
        return False
    else:
        return True


#The function will check that the given date is not a present date.
def check_if_not_present_date(date):
    formatted_date = convert_date_formats(date)
    now = datetime.now().date()

    if formatted_date == now:
        return False
    else:
        return True


#The function will check that the given date is valid
def check_if_valid_date(date):
    if date:
        try:
            parse(date)
            return True
        except:
            return False
    return False


# The function will check that the given field is not null
def check_if_not_null_value(value):
    try:
        if value is None:
            return False
        else:
            return True
    except NameError:
        return False


#The function will check that the given field is not blank
def check_if_not_blank_value(value):
    if str(value) == "":
        return False
    elif value is None:
        return True
    elif str(value).strip():
        return True
    else:
        return True


#The function will check that the given array field is not null
def check_if_array_not_null_value(value):
    try:
        if not value:
            return False
        else:
            return True
    except NameError:
        return False


# The function will convert incoming date formats to a django supported date value
def convert_date_formats(date):
    value = None
    if date != "":
        for date_format in ('%Y%m%d','%Y-%m-%d','%d.%m.%Y', '%d/%m/%Y', '%Y.%m.%d','%Y/%m/%d', '%d-%m-%Y', '%dd-%mm-%yy'):
            try:
                date = datetime.strptime(date, date_format).strftime('%Y-%m-%d')
                return datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                value = ""
        return value
    else:
        return None


#The function will validate the received payload against all defined functions for the specific payload
def validate_received_payload(data):
    message_type = data["messageType"].strip()
    org_name = data["orgName"].strip()
    facility_hfr_code = data["facilityHfrCode"].strip()
    data_items = data["items"]

    status = check_if_payload_exists(message_type, facility_hfr_code)
    d = dict()

    if status is False:
        instance_transaction_summary = TransactionSummary()
        instance_transaction_summary.date_time_created = datetime.now()
        instance_transaction_summary.message_type = message_type
        instance_transaction_summary.org_name = org_name
        instance_transaction_summary.facility_hfr_code = facility_hfr_code
        instance_transaction_summary.save()

        transaction_id = instance_transaction_summary.id

        validation_rule_failed = 0
        total_passed_records = 0
        total_failed_records = 0
        transaction_status = True
        error_message = []
        transaction_status_array = []
        total_payload_transactions_status_array = []

        instance_message_type = PayloadThreshold.objects.filter(payload_code=message_type).first()

        allowed_threshold = instance_message_type.percentage_threshold

        for val in data_items:
            rules = FieldValidationMapping.objects.filter(message_type=message_type)
            for rule in rules:
                field = rule.field
                predefined_rule = ValidationRule.objects.get(id=rule.validation_rule_id)
                rule_name = predefined_rule.rule_name

                # Convert date format
                try:
                    if rule_name == "convert_date_formats":
                        date = convert_date_formats(val[field])
                        logging.debug(date)
                        if date == "":
                            raised_error = "Failed to convert " + field + " with value of " + val[
                                field] + " to a valid date format."
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                        else:
                            transaction_status = True
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Failed to convert "+field+" with value of "+val[field]+" to a valid date format."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if it is a future date. Will return True if future date
                try:
                    if rule_name == "check_if_not_future_date":
                        response = check_if_not_future_date(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Field " + field + " with value of " + val[
                                field] + " seems to be a future date"
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Date Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if it is a past date. Will return True if past date
                try:
                    if rule_name == "check_if_not_past_date":
                        response = check_if_not_past_date(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Date Field " + field + " with value of " + val[
                                field] + " seems to be a past date"
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if it is a present date. Will return True if present date
                try:
                    if rule_name == "check_if_not_present_date":
                        response = check_if_not_present_date(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Date Field " + field + " with value of " + val[
                                field] + " seems to be a present date."
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if it is a valid date. Will return True if valid
                try:
                    if rule_name == "check_if_valid_date":
                        response = check_if_valid_date(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Date Field " + field + " with value of " + val[
                                field] + " is invalid"
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Date Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if not null value
                try:
                    if rule_name == "check_if_not_null_value":
                        response = check_if_not_null_value(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Field " + field + " with value of " + val[
                                field] + " cannot be null"
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                # Check if not blank value
                try:
                    if rule_name == "check_if_not_blank_value":
                        response = check_if_not_blank_value(val[field])

                        if response is True:
                            transaction_status = True
                        else:
                            raised_error = "Field " + field + " with value of " + val[
                                field] + " cannot be blank"
                            transaction_status = False
                            validation_rule_failed += 1
                            error_message.append(raised_error)
                except (NameError, TypeError, RuntimeError, KeyError, ValueError):
                    raised_error = "Field " + field + " with value of " + val[
                        field] + " is invalid."
                    transaction_status = False
                    validation_rule_failed += 1
                    error_message.append(raised_error)

                transaction_status_array.append(transaction_status)
                total_payload_transactions_status_array.append(transaction_status)

            previous_transaction = TransactionSummary.objects.get(
                id=instance_transaction_summary.id)

            if validation_rule_failed > 0:
                previous_transaction.total_failed += 1
                total_failed_records +=1
            else:
                previous_transaction.total_passed += 1
                total_passed_records +=1

            previous_transaction.save()

            instance_transaction_summary_lines = TransactionSummaryLine()
            instance_transaction_summary_lines.transaction_id = transaction_id
            instance_transaction_summary_lines.payload_object = json.dumps(val)

            if False in transaction_status_array:
                instance_transaction_summary_lines.transaction_status = False
            else:
                instance_transaction_summary_lines.transaction_status = True
            instance_transaction_summary_lines.error_message = error_message

            instance_transaction_summary_lines.save()

            # initialize check
            validation_rule_failed = 0
            transaction_status_array = []
            error_message = []

        # return the value of array statuses based on allowed threshold
        calculated_threshold = calculate_threshold(total_failed_records, total_passed_records)

        # transaction_status = False

        if False in total_payload_transactions_status_array and calculated_threshold >= allowed_threshold:
            transaction_status = True
        elif False in total_payload_transactions_status_array and calculated_threshold < allowed_threshold:
            transaction_status = False
        else:
            transaction_status  = True

        d["transaction_status"] = transaction_status
        d["transaction_id"] = transaction_id
    else:
        d["transaction_status"] = False
        d["transaction_id"] = 0

    return d


#The function will calculate the threshold for a specific payload and return a percentage
def calculate_threshold(total_failed, total_passed):
    calculated_threshold = 0
    if total_failed != 0 and total_passed != 0:
        calculated_threshold = (total_passed/(total_failed + total_passed)) * 100
    elif total_passed == 0 and total_failed != 0:
        calculated_threshold = 0
    elif total_passed != 0 and total_failed == 0:
        calculated_threshold = 100

    return calculated_threshold


#The function will determine if a payload was already created in Transaction Summary
def check_if_payload_exists(message_type,facility_hfr_code):
    today = date.today()
    tz = pytz.timezone('Africa/Dar_es_Salaam')
    midnight = datetime.combine(today, datetime.min.time())

    midnight_aware = pytz.utc.localize(midnight)

    transaction = TransactionSummary.objects.filter(message_type__exact=message_type, facility_hfr_code=facility_hfr_code,
                                                    transaction_date_time__gte = midnight_aware, is_active=True)

    facility = master_data_models.Facility.objects.filter(facility_hfr_code=facility_hfr_code).first()

    is_cpt_mapped = facility.uses_cpt_internally

    if transaction.count() == 0: #Payload not created
        return False
    elif transaction.count() > 0 and is_cpt_mapped == False:
        return True # CSV files exists so stop transaction
    elif transaction.count() > 0 and is_cpt_mapped == True:
        return False #uses API allow as many transactions as needed.
    else:
        return True


