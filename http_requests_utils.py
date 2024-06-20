import requests
import time
import json
import logging
from .logging_utils import handle_errors
from .data_processing_utils import process_costs, get_analysis_timeframe

def build_cost_management_request(subscription_id, grouping_type, grouping_name, access_token):
    """
    Build the request for the Azure Cost Management API.

    Returns:
        tuple: URL, payload, and headers for the API request.
    """
    cost_management_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2021-10-01'

    start_date, end_date, timeframe = get_analysis_timeframe()

    payload = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": timeframe,
        "dataset": {
            "granularity": "Daily",
            "aggregation": {
                "totalCost": {
                    "name": "Cost",
                    "function": "Sum"
                }
            },
            "grouping": [
                {
                    "type": grouping_type,
                    "name": grouping_name
                }
            ]
        }
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    return cost_management_url, payload, headers

def request_and_process(url, headers, payload, subscription_name):
    """
    Send request to the Azure Cost Management API and process the response.

    Args:
        url (str): The API URL.
        headers (dict): The request headers.
        payload (dict): The request payload.
        subscription_name (str): The name of the subscription.

    Returns:
        dict or None: The response data or None if no cost found.
    """
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        time.sleep(1)  # Pausa de 1 segundos entre as requisições
    except requests.exceptions.RequestException as e:
        handle_errors(e, f"Failed to retrieve cost data for subscription '{subscription_name}'")

    try:
        data = response.json()
        logging.debug(f"Received data: {json.dumps(data, indent=2)}")
    except json.JSONDecodeError as e:
        handle_errors(e, "JSON decode error")

    if 'properties' not in data or 'rows' not in data['properties']:
        logging.info("No Cost Found in the response data.")
        return None, 0

    return data
