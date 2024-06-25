import argparse
import logging
import sys

from utils import (analyze_subscription, get_access_token,
                   get_subscription_ids, save_execution_result, setup_logging)


def main():
    parser = argparse.ArgumentParser(description='Analyze Azure costs by group or tag with optional alert generation')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('analysis_type', type=str, choices=['grupo', 'tag'], help='Type of analysis: "grupo" or "tag"')
    parser.add_argument('grouping_key', type=str, help='Grouping key for the analysis (e.g., ServiceName, Projeto)')
    parser.add_argument('--alert', action='store_true', help='Enable alert mode to generate alerts for high costs')
    parser.add_argument('--csv', action='store_true', help='Save results to a CSV file')
    parser.add_argument('--date', type=str, help='Start date for the analysis period in YYYY-MM-DD format')

    args = parser.parse_args()

    setup_logging()

    subscription_prefix = args.subscription_prefix
    analysis_type = args.analysis_type
    grouping_key = args.grouping_key
    alert_mode = args.alert
    save_csv = args.csv
    start_date_str = args.date

    logging.info(f"Starting analysis for {analysis_type} with grouping key: {grouping_key} and subscription prefix: {subscription_prefix}")

    try:
        access_token = get_access_token()
        logging.info("Access token generated successfully.")

        subscription_ids = get_subscription_ids(subscription_prefix)
        subscription_results = {}

        for subscription_name, subscription_id in subscription_ids:
            sub_name, df, result = analyze_subscription(subscription_name, subscription_id, analysis_type, grouping_key, access_token, alert_mode, start_date_str)
            if df is not None:
                subscription_results[sub_name] = df
            logging.info(result)

        if save_csv and subscription_results:
            save_execution_result("sucesso", subscription_results)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

