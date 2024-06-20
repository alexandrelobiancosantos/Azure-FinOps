import subprocess
import json
import requests
import time
from datetime import datetime, timedelta
import statistics
import pandas as pd
from tabulate import tabulate
import logging

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(level=logging.INFO)

def handle_errors(exception, message):
    """Handle errors by logging the message and exception, then exiting the program."""
    logging.error(f"{message}: {exception}")
    exit(1)

# Funções que interagem com o Azure CLI

def get_subscription_ids(subscription_prefix):
    """
    Retrieve subscription IDs that start with the given prefix.
    Returns:
        list of tuples: List of subscription names and IDs.
    """
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
    """
    Retrieve an access token for the Azure management API.

    Returns:
        str: The access token.
    """
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

# Funções que processam os dados

def get_analysis_timeframe():
    """
    Get the analysis timeframe from the current date to seven days ago.

    Returns:
        tuple: Start date, end date, and timeframe dictionary.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    timeframe = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d')
    }
    return start_date, end_date, timeframe

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

def check_alert(cost_yesterday, average_cost):
    """
    Check if the cost for yesterday exceeds the average cost.
    Returns:
        str: "Yes" if cost_yesterday exceeds average_cost, otherwise "No".
    """
    return "Yes" if cost_yesterday > average_cost else "No"

def process_costs(costs_by_group, grouping_key, start_date, end_date, yesterday_str):
    """
    Process costs by group and calculate average costs, alerts, and additional metrics.

    Args:
        costs_by_group (dict): The costs grouped by a specific key.
        grouping_key (str): The key to group costs by.
        start_date (datetime): The start date for the analysis period.
        end_date (datetime): The end date for the analysis period.
        yesterday_str (str): The string representation of yesterday's date.

    Returns:
        list: List of results with average costs, alerts, and additional metrics.
    """
    results = []

    for group_value, costs in costs_by_group.items():
        cost_values = [cost for date, cost in costs]
        average_cost = statistics.mean(cost_values)
        cost_yesterday = next((cost for date, cost in costs if date == int(yesterday_str)), 0)
        alert = check_alert(cost_yesterday, average_cost)
        percent_variation = ((cost_yesterday - average_cost) / average_cost) * 100 if average_cost != 0 else 0
        cost_difference = cost_yesterday - average_cost

        results.append({
            grouping_key: group_value,
            "Average Cost": average_cost,
            "Cost Yesterday": cost_yesterday,
            "Alert": alert,
            "Percent Variation": percent_variation,
            "Cost Difference": cost_difference,
            "Period of Average Calculation": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Analysis Date": datetime.utcnow().strftime('%Y-%m-%d')
        })

    return results

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

def analyze_costs(subscription_name, subscription_id, grouping_dimension, access_token):
    """
    Analyze costs for a subscription grouped by a specific dimension.
    Returns:
        tuple: Analysis result as a table, total cost yesterday, and the dataframe.
    """
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
    """
    Analyze costs for a subscription grouped by a specific tag key.

    Returns:
        tuple: Analysis result as a table, total cost yesterday, and the dataframe.
    """
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
    
    csv_filename = f"{filename_base}.csv"

    if dataframe is not None:
        dataframe.to_csv(csv_filename, index=False, sep='*', float_format='%.2f', decimal=',')

def analyze_subscription(subscription_name, subscription_id, analysis_type, grouping_key, access_token, alert_mode=False):
    final_result = ""
    total_cost_yesterday = 0
    
    logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

    if analysis_type.lower() == 'tag':
        result, cost_yesterday, df = analyze_costs_by_tag(subscription_name, subscription_id, grouping_key, access_token)
    else:
        result, cost_yesterday, df = analyze_costs(subscription_name, subscription_id, grouping_key, access_token)

    total_cost_yesterday += cost_yesterday

    if alert_mode and df is not None:
        alert_df = df[df['Alert'] == 'Yes']
        if not alert_df.empty:
            print(alert_df)
            alert_result = tabulate(alert_df, headers='keys', tablefmt='plain', floatfmt='.3f')
            final_result += alert_result + "\n"
            save_execution_result("sucesso", subscription_name, analysis_type, total_cost_yesterday, ["Yes"], final_result, alert_df)
    else:
        print(result)
        print(f"Total cost yesterday: {total_cost_yesterday:.2f}")
        final_result += result + "\n"
        save_execution_result("sucesso", subscription_name, analysis_type, total_cost_yesterday, [], final_result, df)

    return total_cost_yesterday
