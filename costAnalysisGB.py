import sys
import logging
from utils import get_access_token, get_subscription_ids, analyze_costs, analyze_costs_by_tag, setup_logging, save_execution_result

def main():
    setup_logging()
    subscription_prefix = sys.argv[1]
    analysis_type = sys.argv[2]

    logging.info(f"Starting analysis for subscription prefix: {subscription_prefix} and analysis type: {analysis_type}")

    try:
        access_token = get_access_token()
        logging.info("Access token generated successfully.")

        subscription_ids = get_subscription_ids(subscription_prefix)

        for subscription_name, subscription_id in subscription_ids:
            logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

            if analysis_type.lower() == 'tag':
                result, total_cost_yesterday = analyze_costs_by_tag(subscription_name, subscription_id, 'TagKey', access_token)
            else:
                result, total_cost_yesterday = analyze_costs(subscription_name, subscription_id, analysis_type, access_token)

            print(result)
            print(f"Total cost yesterday: {total_cost_yesterday:.2f}")

        save_execution_result("sucesso")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        save_execution_result("falha")
        sys.exit(1)

if __name__ == "__main__":
    main()
