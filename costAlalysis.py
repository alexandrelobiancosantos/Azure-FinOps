import logging
import argparse
from utils import get_access_token, get_subscription_ids, analyze_costs, setup_logging

def main():
    # Configuração do parsing de argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Analyze Azure costs')
    parser.add_argument('analysis_type', type=str, help='Type of analysis (e.g., ServiceName, ResourceGroup, MeterCategory)')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')

    args = parser.parse_args()

    # Configuração do logging
    setup_logging()

    analysis_type = args.analysis_type
    subscription_prefix = args.subscription_prefix

    logging.info(f"Starting analysis for type: {analysis_type} and subscription prefix: {subscription_prefix}")

    access_token = get_access_token()
    subscription_ids = get_subscription_ids(subscription_prefix)

    for subscription_name, subscription_id in subscription_ids:
        logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

        result, total_cost_yesterday = analyze_costs(subscription_name, subscription_id, analysis_type, access_token)
        logging.info(f"Total Cost Yesterday: R$ {total_cost_yesterday:.3f}")
        logging.info(f"\nCost analysis by {analysis_type}:")

        if result is None:
            logging.info("No data available due to an error or invalid grouping dimension.")
        elif isinstance(result, str):
            logging.info(result)
        else:
            logging.info("\n" + result)

if __name__ == "__main__":
    main()
