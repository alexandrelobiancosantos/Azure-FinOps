"""
Módulo para análise de custos de assinaturas do Azure agrupados por uma chave de tag específica.

Este script fornece funções para analisar os custos diários associados a diferentes assinaturas do Azure,
agrupados por uma chave de tag específica. Ele utiliza a API do Azure para coletar dados e gerar relatórios 
de custos, incluindo verificações de alerta se os custos de ontem excederem a média dos últimos sete dias.

Funções principais:
- analyze_subscription_by_tag: Analisa os custos de uma assinatura específica agrupados por uma chave de tag.
- main: Configura e inicia o processo de análise com base em argumentos fornecidos via linha de comando.
"""
import logging
import argparse
from utils import get_access_token, get_subscription_ids, analyze_costs_by_tag, setup_logging, save_execution_result

def analyze_subscription_by_tag(subscription_name, subscription_id, tag_key, access_token):
    alerts = []
    final_result = ""
    total_cost_yesterday = 0
    
    logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

    result, cost_yesterday, df = analyze_costs_by_tag(subscription_name, subscription_id, tag_key, access_token)
    total_cost_yesterday += cost_yesterday
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
    
    final_result += result + "\n"

    save_execution_result("sucesso", subscription_name, tag_key, total_cost_yesterday, alerts, final_result, df)
    return total_cost_yesterday

def main():
    parser = argparse.ArgumentParser(description='Analyze Azure costs by tag')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('tag_key', type=str, help='Tag key to group costs by')

    args = parser.parse_args()

    setup_logging()

    subscription_prefix = args.subscription_prefix
    tag_key = args.tag_key

    logging.info(f"Starting analysis for tag key: {tag_key} and subscription prefix: {subscription_prefix}")

    try:
        access_token = get_access_token()
        subscription_ids = get_subscription_ids(subscription_prefix)

        for subscription_name, subscription_id in subscription_ids:
            analyze_subscription_by_tag(subscription_name, subscription_id, tag_key, access_token)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        save_execution_result("falha", "general")
        exit(1)

if __name__ == "__main__":
    main()

