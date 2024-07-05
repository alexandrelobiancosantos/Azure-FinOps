import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests

from utils import (get_access_token, get_subscription_ids, handle_errors,
                   setup_logging)


def get_resources(subscription_id, access_token):
    """
    Retrieve resources for a given subscription.

    Args:
        subscription_id (str): The ID of the subscription.
        access_token (str): The Azure access token.

    Returns:
        list: A list of resources.
    """
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resources?api-version=2021-04-01"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        handle_errors(e, f"Failed to retrieve resources for subscription '{subscription_id}'")
        return []
    except json.JSONDecodeError as e:
        handle_errors(e, "JSON decode error")
        return []

    return data.get('value', [])

def get_resource_tags(resource_id, access_token):
    """
    Retrieve tags for a given resource.

    Args:
        resource_id (str): The ID of the resource.
        access_token (str): The Azure access token.

    Returns:
        list: A list of dictionaries containing tag keys and values.
    """
    url = f"https://management.azure.com{resource_id}/providers/Microsoft.Resources/tags/default?api-version=2021-04-01"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        handle_errors(e, f"Failed to retrieve tags for resource '{resource_id}'")
        return []
    except json.JSONDecodeError as e:
        handle_errors(e, "JSON decode error")
        return []

    tags = []
    tag_properties = data.get('properties', {}).get('tags', {})
    for tag_name, tag_value in tag_properties.items():
        tags.append({
            'TagKey': tag_name,
            'TagValue': tag_value
        })
    return tags

def main():
    parser = argparse.ArgumentParser(description='Generate a list of tags for resources within Azure subscriptions')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('--date', type=str, help='Date for the analysis in YYYY-MM-DD format')
    args = parser.parse_args()
    
    setup_logging()
    subscription_prefix = args.subscription_prefix
    analysis_date = args.date

    if not analysis_date:
        analysis_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    logging.info(f"Starting tag analysis for subscriptions with prefix '{subscription_prefix}' on date '{analysis_date}'")
    
    try:
        access_token = get_access_token()
        subscription_ids = get_subscription_ids(subscription_prefix)
        
        results = []
        for subscription_name, subscription_id in subscription_ids:
            logging.info(f"Analyzing subscription: {subscription_name} with ID: {subscription_id}")
            resources = get_resources(subscription_id, access_token)
            for resource in resources:
                resource_id = resource['id']
                resource_name = resource['name']
                logging.info(f"Analyzing resource: {resource_name} with ID: {resource_id}")
                tags = get_resource_tags(resource_id, access_token)
                for tag in tags:
                    results.append({
                        'Subscription': subscription_name,
                        'ResourceName': resource_name,
                        'TagKey': tag['TagKey'],
                        'TagValue': tag['TagValue']
                    })
                # Sleep to avoid too many requests
                time.sleep(2)
        
        if results:
            df = pd.DataFrame(results)
            print(df.to_string(index=False))
        else:
            logging.info("No tags found for the specified subscriptions.")
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

