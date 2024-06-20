"""
Módulo para análise de alertas de custos de assinaturas do Azure agrupados por dimensões ou chaves de tag específicas.

Este script fornece funções para analisar os custos diários associados a diferentes assinaturas do Azure,
agrupados por uma dimensão ou uma chave de tag específica, e gerar alertas se os custos de ontem excederem 
a média dos últimos sete dias. Apenas os resultados que atendem à condição de alerta ("Yes") serão impressos e salvos.

Funções principais:
- analyze_subscription: Analisa os custos de uma assinatura específica agrupados por uma dimensão ou chave de tag e filtra alertas.
- main: Configura e inicia o processo de análise com base em argumentos fornecidos via linha de comando.

Instruções para executar:

Para análise por tag:
    python alert.py tag "subscrição" "chave da tag"

Para análise por grupo:
    python alert.py grupo "subscrição" "ServiceName"
"""

import sys
import logging
import argparse
from tabulate import tabulate
from utils import get_access_token, get_subscription_ids, analyze_costs, analyze_costs_by_tag, setup_logging, save_execution_result
import pandas as pd

def analyze_subscription(subscription_name, subscription_id, analysis_type, grouping_key, access_token):
    final_result = ""
    total_cost_yesterday = 0
    
    logging.info(f"\nAnalyzing subscription: {subscription_name} with ID: {subscription_id}")

    if analysis_type.lower() == 'tag':
        result, cost_yesterday, df = analyze_costs_by_tag(subscription_name, subscription_id, grouping_key, access_token)
    else:
        result, cost_yesterday, df = analyze_costs(subscription_name, subscription_id, grouping_key, access_token)

    total_cost_yesterday += cost_yesterday

    if df is not None:
        alert_df = df[df['Alert'] == 'Yes']
        if not alert_df.empty:
            print(alert_df)
            alert_result = tabulate(alert_df, headers='keys', tablefmt='plain', floatfmt='.3f')
            final_result += alert_result + "\n"
            save_execution_result("sucesso", subscription_name, analysis_type, total_cost_yesterday, ["Yes"], final_result, alert_df)

    return total_cost_yesterday

def main():
    parser = argparse.ArgumentParser(description='Analyze Azure cost alerts by group or tag')
    parser.add_argument('analysis_type', type=str, choices=['grupo', 'tag'], help='Type of analysis: "grupo" or "tag"')
    parser.add_argument('subscription_prefix', type=str, help='Prefix of the subscription to analyze')
    parser.add_argument('grouping_key', type=str, help='Grouping key for the analysis (e.g., ServiceName, Projeto)')

    args = parser.parse_args()

    setup_logging()

    analysis_type = args.analysis_type
    subscription_prefix = args.subscription_prefix
    grouping_key = args.grouping_key

    logging.info(f"Starting alert analysis for {analysis_type} with grouping key: {grouping_key} and subscription prefix: {subscription_prefix}")

    try:
        access_token = get_access_token()
        logging.info("Access token generated successfully.")

        subscription_ids = get_subscription_ids(subscription_prefix)

        for subscription_name, subscription_id in subscription_ids:
            analyze_subscription(subscription_name, subscription_id, analysis_type, grouping_key, access_token)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        save_execution_result("falha", "general")
        sys.exit(1)

if __name__ == "__main__":
    main()
