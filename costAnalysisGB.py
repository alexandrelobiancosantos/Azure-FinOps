"""
Módulo para análise de custos de assinaturas do Azure agrupados por dimensões específicas.

Este script fornece funções para analisar os custos diários associados a diferentes assinaturas do Azure,
agrupados por uma dimensão específica. Ele utiliza a API do Azure para coletar dados e gerar relatórios 
de custos, incluindo verificações de alerta se os custos de ontem excederem a média dos últimos sete dias.

Funções principais:
- analyze_subscription: Analisa os custos de uma assinatura específica agrupados por uma dimensão.
- main: Configura e inicia o processo de análise com base em argumentos fornecidos via linha de comando.
"""

import sys
import logging
from utils import get_access_token, get_subscription_ids, analyze_costs, analyze_costs_by_tag, setup_logging, save_execution_result

def analyze_subscription(subscription_name, subscription_id, analysis_type, access_token):
    alerts = []
    final_result = ""
    total_cost_yesterday = 0
    
    logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

    if analysis_type.lower() == 'tag':
        result, cost_yesterday, df = analyze_costs_by_tag(subscription_name, subscription_id, 'TagKey', access_token)
    else:
        result, cost_yesterday, df = analyze_costs(subscription_name, subscription_id, analysis_type, access_token)

    total_cost_yesterday += cost_yesterday

    if "Yes" in result:
        alerts.append(subscription_name)

    print(result)
    print(f"Total cost yesterday: {total_cost_yesterday:.2f}")
    
    final_result += result + "\n"

    save_execution_result("sucesso", subscription_name, analysis_type, total_cost_yesterday, alerts, final_result, df)
    return total_cost_yesterday

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
            analyze_subscription(subscription_name, subscription_id, analysis_type, access_token)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        save_execution_result("falha", "general")
        sys.exit(1)

if __name__ == "__main__":
    main()


