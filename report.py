import argparse
import logging
import sys
import time

from utils import (analyze_subscription, find_common_prefix, get_access_token,
                   get_subscription_ids, save_execution_result, setup_logging)


def main():
    parser = argparse.ArgumentParser(description='Analyze Azure costs by group, tag, or subscription with optional alert generation')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('analysis_type', type=str, choices=['group', 'tag', 'subscription'], help='Type of analysis: "group", "tag", or "subscription"')
    parser.add_argument('grouping_key', type=str, nargs='?', help='Grouping key for the analysis (e.g., ServiceName, Projeto)')
    parser.add_argument('--alert', action='store_true', help='Enable alert mode to generate alerts for high costs')
    parser.add_argument('--save', action='store_true', help='Save results to a CSV file')
    parser.add_argument('--date', type=str, help='Start date for the analysis period in YYYY-MM-DD format')
    parser.add_argument('--period', type=int, default=31, help='Number of days for the analysis period')
    args = parser.parse_args()
    setup_logging()
    subscription_prefix = args.subscription_prefix
    analysis_type = args.analysis_type
    grouping_key = args.grouping_key
    alert_mode = args.alert
    save_xlsx = args.save
    start_date_str = args.date
    period = args.period

    try:
        access_token = get_access_token()
        subscription_ids = get_subscription_ids(subscription_prefix)
        subscription_results = {}
        subscription_names = [name for name, _ in subscription_ids]
        common_prefix = find_common_prefix(subscription_names)
        for subscription_name, subscription_id in subscription_ids:
            short_name = subscription_name.replace(common_prefix, '').strip()
            sub_name, df, result = analyze_subscription(subscription_name, subscription_id, analysis_type, grouping_key, access_token, alert_mode, start_date_str, period)
            if df is not None:
                subscription_results[short_name] = df
            logging.info(result)
            time.sleep(2)  # Sleep for 2 seconds
        if save_xlsx and subscription_results:
            save_execution_result("sucesso", subscription_results, common_prefix, grouping_key)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


