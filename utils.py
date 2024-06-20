import subprocess
import json
import requests
from datetime import datetime, timedelta
import statistics
import pandas as pd
from tabulate import tabulate
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def handle_errors(exception, message):
    logging.error(f"{message}: {exception}")
    exit(1)

def get_subscription_ids(subscription_prefix):
    try:
        result = subprocess.run(
            ["az", "account", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        subscriptions = json.loads(result.stdout)
        subscription_ids = [
            (subscription['name'], subscription['id'])
            for subscription in subscriptions
            if subscription['name'].startswith(subscription_prefix)
        ]
        if not subscription_ids:
            logging.error(f"No subscriptions found with prefix '{subscription_prefix}'.")
            exit(1)
        return subscription_ids
    except subprocess.CalledProcessError as e:
        handle_errors(e, "Command error")
    except json.JSONDecodeError as e:
        handle_errors(e, "JSON decode error")
    except Exception as e:
        handle_errors(e, "Unexpected error")

def get_access_token():
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource=https://management.azure.com/"],
            capture_output=True,
            text=True,
            check=True
        )
        token_info = json.loads(result.stdout)
        logging.info(f"Access token generated successfully.")
        return token_info['accessToken']
    except subprocess.CalledProcessError as e:
        handle_errors(e, "Command error")
    except json.JSONDecodeError as e:
        handle_errors(e, "JSON decode error")
    except Exception as e:
        handle_errors(e, "Unexpected error")

def get_analysis_timeframe():
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    timeframe = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d')
    }
    return start_date, end_date, timeframe

def build_cost_management_request(subscription_id, grouping_type, grouping_name, access_token):
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

def check_alert(cost_yesterday, average_cost):
    return "Yes" if cost_yesterday > average_cost else "No"

def process_costs(costs_by_group, grouping_key, start_date, end_date, yesterday_str):
    results = []

    for group_value, costs in costs_by_group.items():
        cost_values = [cost for date, cost in costs]
        average_cost = statistics.mean(cost_values)
        cost_yesterday = next((cost for date, cost in costs if date == int(yesterday_str)), 0)
        alert = check_alert(cost_yesterday, average_cost)
        results.append({
            grouping_key: group_value,
            "Average Cost": average_cost,
            "Cost Yesterday": cost_yesterday,
            "Alert": alert,
            "Period of Average Calculation": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Analysis Date": datetime.utcnow().strftime('%Y-%m-%d')
        })

    return results

def request_and_process(url, headers, payload, subscription_name):
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
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

def analyze_costs(subscription_name, subscription_id, grouping_dimension, access_token):
    cost_management_url, payload, headers = build_cost_management_request(subscription_id, 'Dimension', grouping_dimension, access_token)

    start_date, end_date, _ = get_analysis_timeframe()

    logging.debug(f"Sending request to Cost Management API for subscription {subscription_id} with payload: {json.dumps(payload, indent=2)}")

    data = request_and_process(cost_management_url, headers, payload, subscription_name)

    if data is None:
        return "No Cost Found", 0, None

    costs_by_group = {}
    total_cost_yesterday = 0
    yesterday_str = (end_date - timedelta(days=1)).strftime('%Y%m%d')

    for result in data['properties']['rows']:
        cost = float(result[0])
        date = result[1]
        group = result[2]

        if group not in costs_by_group:
            costs_by_group[group] = []
        costs_by_group[group].append((date, cost))

        if date == int(yesterday_str):
            total_cost_yesterday += cost

    results = process_costs(costs_by_group, grouping_dimension, start_date, end_date, yesterday_str)

    df = pd.DataFrame(results)

    if df.empty:
        logging.info("No data to display.")
        return "No Cost Found", total_cost_yesterday, None

    table = tabulate(df, headers='keys', tablefmt='plain', floatfmt='.3f')
    return table, total_cost_yesterday, df


def analyze_costs_by_tag(subscription_name, subscription_id, tag_key, access_token):
    cost_management_url, payload, headers = build_cost_management_request(subscription_id, 'TagKey', tag_key, access_token)

    start_date, end_date, _ = get_analysis_timeframe()

    logging.debug(f"Sending request to Cost Management API for subscription {subscription_id} with payload: {json.dumps(payload, indent=2)}")

    data = request_and_process(cost_management_url, headers, payload, subscription_name)

    if data is None:
        return "No Cost Found", 0, None

    costs_by_tag = {}
    total_cost_yesterday = 0
    yesterday_str = (end_date - timedelta(days=1)).strftime('%Y%m%d')

    for result in data['properties']['rows']:
        cost = float(result[0])
        date = result[1]
        tag_value = result[3]

        if tag_value:
            if tag_value not in costs_by_tag:
                costs_by_tag[tag_value] = []
            costs_by_tag[tag_value].append((date, cost))

            if date == int(yesterday_str):
                total_cost_yesterday += cost

    results = process_costs(costs_by_tag, tag_key, start_date, end_date, yesterday_str)

    df = pd.DataFrame(results)

    if df.empty:
        logging.info("No data to display.")
        return "No Cost Found", total_cost_yesterday, None

    table = tabulate(df, headers='keys', tablefmt='plain', floatfmt='.3f')
    return table, total_cost_yesterday, df


def save_execution_result(status, subscription_name, analysis_type=None, total_cost_yesterday=None, alerts=None, table=None, dataframe=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    analysis_part = f"_{analysis_type}" if analysis_type else ""
    filename_base = f"{subscription_name}{analysis_part}_{timestamp}"
    
    # txt_filename = f"{filename_base}.txt"
    csv_filename = f"{filename_base}.csv"

    # with open(txt_filename, 'w') as file:
    #     if total_cost_yesterday is not None:
    #         file.write(f"Total cost yesterday: {total_cost_yesterday:.2f}\n")
    #     if alerts:
    #         for alert in alerts:
    #             file.write(f"{alert}\n")
    #     if table:
    #         file.write(table)

    if dataframe is not None:
        dataframe.to_csv(csv_filename, index=False, sep='*', float_format='%.2f', decimal=',')


