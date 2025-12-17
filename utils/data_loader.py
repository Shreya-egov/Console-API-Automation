import json
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def get_tomorrow_timestamp():
    """
    Get tomorrow's date at midnight as a Unix timestamp in milliseconds.
    """
    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int(tomorrow.timestamp() * 1000)


def get_one_month_later_timestamp():
    """
    Get the date one month after tomorrow at 23:59:59 as a Unix timestamp in milliseconds.
    """
    tomorrow = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=1)
    one_month_later = tomorrow + relativedelta(months=1)
    return int(one_month_later.timestamp() * 1000)


def get_tomorrow_iso():
    """
    Get tomorrow's date in ISO format (for cycleData).
    """
    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def get_one_month_later_iso():
    """
    Get the date one month after tomorrow in ISO format (for cycleData).
    """
    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    one_month_later = tomorrow + relativedelta(months=1)
    return one_month_later.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def apply_dynamic_dates(payload):
    """
    Apply dynamic dates to a campaign payload.
    Sets startDate to tomorrow and endDate to one month after.
    """
    start_ts = get_tomorrow_timestamp()
    end_ts = get_one_month_later_timestamp()
    start_iso = get_tomorrow_iso()
    end_iso = get_one_month_later_iso()

    if "CampaignDetails" in payload:
        details = payload["CampaignDetails"]

        # Update campaign level dates
        if "startDate" in details:
            details["startDate"] = start_ts
        if "endDate" in details:
            details["endDate"] = end_ts

        # Update cycle dates in deliveryRules
        if "deliveryRules" in details:
            for rule in details["deliveryRules"]:
                if "cycles" in rule:
                    for cycle in rule["cycles"]:
                        if "startDate" in cycle:
                            cycle["startDate"] = start_ts
                        if "endDate" in cycle:
                            cycle["endDate"] = end_ts

        # Update cycleData ISO dates in additionalDetails
        if "additionalDetails" in details:
            add_details = details["additionalDetails"]
            if "cycleData" in add_details and "cycleData" in add_details["cycleData"]:
                for cycle_data in add_details["cycleData"]["cycleData"]:
                    if "fromDate" in cycle_data:
                        cycle_data["fromDate"] = start_iso
                    if "toDate" in cycle_data:
                        cycle_data["toDate"] = end_iso

    return payload


def load_payload(service_name, filename):
    """
    Load a JSON payload file from the payloads/<service_name>/ directory.
    
    Args:
        service_name (str): The name of the microservice folder (e.g., 'household')
        filename (str): The JSON file name (e.g., 'create_household.json')
    
    Returns:
        dict: The loaded JSON as a Python dictionary.
    """
    base_path = os.path.dirname(__file__)  # current directory: utils/
    file_path = os.path.join(base_path, "..", "payloads", service_name, filename)

    with open(os.path.abspath(file_path), 'r', encoding='utf-8') as f:
        return json.load(f)
