import logging
import argparse
import subprocess
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
from tabulate import tabulate
import statistics

def setup_logging():
    logging.basicConfig(level=logging.INFO)

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
        logging.error(f"Command error: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)

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
        logging.error(f"Command error: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)

def analyze_costs_by_tag(subscription_name, subscription_id, tag_key, access_token):
    cost_management_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2021-10-01'

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    timeframe = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d')
    }

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
                    "type": "TagKey",
                    "name": tag_key
                }
            ]
        }
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    logging.debug(f"Sending request to Cost Management API for subscription {subscription_id} with payload: {json.dumps(payload, indent=2)}")

    response = requests.post(cost_management_url, headers=headers, json=payload)

    if response.status_code != 200:
        logging.error(f"Failed to retrieve cost data for subscription '{subscription_name}' with status code {response.status_code}\n{response.text}")
        return None, 0

    try:
        data = response.json()
        logging.debug(f"Received data: {json.dumps(data, indent=2)}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return None, 0

    if 'properties' not in data or 'rows' not in data['properties']:
        logging.info("No Cost Found in the response data.")
        return "No Cost Found", 0

    costs_by_tag = {}
    total_cost_yesterday = 0
    yesterday_str = (end_date - timedelta(days=1)).strftime('%Y%m%d')
    analysis_date = datetime.utcnow().strftime('%Y-%m-%d')

    for result in data['properties']['rows']:
        cost = float(result[0])
        date = result[1]
        tag_value = result[2]

        if tag_value not in costs_by_tag:
            costs_by_tag[tag_value] = []
        costs_by_tag[tag_value].append((date, cost))

        if date == int(yesterday_str):
            total_cost_yesterday += cost

    results = []

    for tag_value, costs in costs_by_tag.items():
        cost_values = [cost for date, cost in costs]
        average_cost = statistics.mean(cost_values)
        std_dev_cost = statistics.stdev(cost_values) if len(cost_values) > 1 else 0
        cost_yesterday = next((cost for date, cost in costs if date == int(yesterday_str)), 0)
        alert = "Yes" if cost_yesterday > (average_cost + std_dev_cost) else "No"
        results.append({
            "Tag Name": tag_value,
            "Average Cost": average_cost,
            "Cost Yesterday": cost_yesterday,
            "Alert": alert,
            "Period of Average Calculation": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Analysis Date": analysis_date
        })

    df = pd.DataFrame(results)

    if df.empty:
        logging.info("No data to display.")
        return "No Cost Found", total_cost_yesterday

    return tabulate(df, headers='keys', tablefmt='grid', floatfmt='.3f'), total_cost_yesterday

def main():
    # Configuração do parsing de argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Analyze Azure costs by tag')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('tag_key', type=str, help='Tag key to group costs by')

    args = parser.parse_args()

    # Configuração do logging
    setup_logging()

    subscription_prefix = args.subscription_prefix
    tag_key = args.tag_key

    logging.info(f"Starting analysis for tag key: {tag_key} and subscription prefix: {subscription_prefix}")

    access_token = get_access_token()
    subscription_ids = get_subscription_ids(subscription_prefix)

    for subscription_name, subscription_id in subscription_ids:
        logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

        result, total_cost_yesterday = analyze_costs_by_tag(subscription_name, subscription_id, tag_key, access_token)
        logging.info(f"Total Cost Yesterday: R$ {total_cost_yesterday:.3f}")
        logging.info(f"\nCost analysis by tag key '{tag_key}':")

        if result is None:
            logging.info("No data available due to an error or invalid grouping dimension.")
        elif isinstance(result, str):
            logging.info(result)
        else:
            logging.info("\n" + result)

if __name__ == "__main__":
    main()
