import logging
import argparse
from utils import get_access_token, get_subscription_ids, analyze_costs_by_tag, setup_logging, save_execution_result

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

    try:
        access_token = get_access_token()
        subscription_ids = get_subscription_ids(subscription_prefix)
        alerts = []

        for subscription_name, subscription_id in subscription_ids:
            logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

            result, total_cost_yesterday = analyze_costs_by_tag(subscription_name, subscription_id, tag_key, access_token)
            logging.info(f"Total Cost Yesterday: {total_cost_yesterday:.2f} R$")
            logging.info(f"\nCost analysis by tag key '{tag_key}':")

            if "Yes" in result:
                alerts.append(subscription_name)

            if result is None:
                logging.info("No data available due to an error or invalid grouping dimension.")
            elif isinstance(result, str):
                logging.info(result)
            else:
                logging.info("\n" + result)

        save_execution_result("sucesso", total_cost_yesterday, alerts)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        save_execution_result("falha")
        exit(1)

if __name__ == "__main__":
    main()
