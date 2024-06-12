import subprocess  # Biblioteca para rodar comandos do sistema
import json  # Biblioteca para trabalhar com dados JSON
import requests  # Biblioteca para fazer requisições HTTP
from datetime import datetime, timedelta  # Biblioteca para trabalhar com datas e tempos
import statistics  # Biblioteca para cálculos estatísticos
import pandas as pd  # Biblioteca para manipulação de dados
from tabulate import tabulate  # Biblioteca para exibição tabular de dados

# Prefixo das assinaturas
subscription_prefix = 'Inicio comum do nome das suas subscrições' #

# Função para obter os IDs das assinaturas que começam com o prefixo fornecido
def get_subscription_ids(subscription_prefix):
    try:
        # Executa o comando do Azure CLI para listar as assinaturas
        result = subprocess.run(
            ["az", "account", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        # Converte a saída do comando (JSON) para um dicionário Python
        subscriptions = json.loads(result.stdout)
        # Encontra as assinaturas que começam com o prefixo fornecido
        subscription_ids = []
        for subscription in subscriptions:
            if subscription['name'].startswith(subscription_prefix):
                subscription_ids.append((subscription['name'], subscription['id']))
        if not subscription_ids:
            print(f"No subscriptions found with prefix '{subscription_prefix}'.")
            exit(1)
        return subscription_ids
    except Exception as e:
        print(f"Failed to obtain subscription IDs: {e}")
        exit(1)

# Função para obter o token de acesso usando a CLI do Azure
def get_access_token():
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource=https://management.azure.com/"],
            capture_output=True,
            text=True,
            check=True
        )
        token_info = json.loads(result.stdout)
        return token_info['accessToken']
    except Exception as e:
        print(f"Failed to obtain token: {e}")
        exit(1)

# Função para realizar a análise de custos
def analyze_costs(subscription_name, subscription_id, grouping_dimension):
    # Define a URL do recurso da API que será consultada para obter os custos
    cost_management_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2021-10-01'

    # Definir o intervalo de tempo para os últimos 7 dias
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    timeframe = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d')
    }

    # Define o payload da solicitação para obter os custos agrupados pela dimensão especificada
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
                    "type": "Dimension",
                    "name": grouping_dimension
                }
            ]
        }
    }

    # Cabeçalhos para a solicitação HTTP
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Faz a solicitação POST para a API REST do Azure Cost Management
    response = requests.post(cost_management_url, headers=headers, json=payload)

    # Verifica se a solicitação foi bem-sucedida
    if response.status_code != 200:
        print(f"Failed to retrieve cost data for subscription '{subscription_name}' with status code {response.status_code}\n{response.text}")
        return None, 0

    # Converte a resposta JSON para um dicionário Python
    data = response.json()

    # Verifica se a resposta contém dados nas propriedades 'properties' e 'rows'
    if 'properties' not in data or 'rows' not in data['properties']:
        return "No Cost Found", 0

    # Dicionário para armazenar os resultados por grupo especificado
    costs_by_group = {}
    total_cost_yesterday = 0

    # Itera sobre cada linha de dados retornados
    for result in data['properties']['rows']:
        cost = float(result[0])
        date = result[1]
        group = result[2]

        if group not in costs_by_group:
            costs_by_group[group] = []
        costs_by_group[group].append((date, cost))

        # Calcula o custo de ontem
        if date == int((end_date - timedelta(days=1)).strftime('%Y%m%d')):
            total_cost_yesterday += cost

    # Lista para armazenar os resultados finais
    results = []

    # Processa os dados para cada grupo especificado
    for group, costs in costs_by_group.items():
        cost_values = [cost for date, cost in costs]
        average_cost = statistics.mean(cost_values)
        std_dev_cost = statistics.stdev(cost_values) if len(cost_values) > 1 else 0
        # Verifica o custo de ontem
        cost_yesterday = next((cost for date, cost in costs if date == int((end_date - timedelta(days=1)).strftime('%Y%m%d'))), 0)
        alert = "Yes" if cost_yesterday > (average_cost + std_dev_cost) else "No"
        # Adiciona os resultados à lista
        results.append({
            grouping_dimension: group,
            "Average Cost": average_cost,
            "Cost Yesterday": cost_yesterday,
            "Alert": alert
        })

    # Converte os resultados em um DataFrame do pandas
    df = pd.DataFrame(results)

    return df, total_cost_yesterday

# Obtém o token de acesso
access_token = get_access_token()

# Obtém os IDs das assinaturas que começam com o prefixo fornecido
subscription_ids = get_subscription_ids(subscription_prefix)

# Itera sobre cada assinatura
for subscription_name, subscription_id in subscription_ids:
    print(f"\nAnalyzing subscription: {subscription_name}")

    # Análise por MeterCategory
    result_meter_category, total_cost_yesterday = analyze_costs(subscription_name, subscription_id, "MeterCategory")
    print(f"Total Cost Yesterday: R$ {total_cost_yesterday:.3f}")
    print("\nCost analysis by MeterCategory:")
    if isinstance(result_meter_category, str):
        print("No Cost Found")
    else:
        print(tabulate(result_meter_category, headers='keys', tablefmt='grid', floatfmt='.3f'))
    
    # Análise por ResourceGroup
    result_resource_group, _ = analyze_costs(subscription_name, subscription_id, "ResourceGroupName")
    print("\nCost analysis by ResourceGroup:")
    if isinstance(result_resource_group, str):
        print("No Cost Found")
    else:
        print(tabulate(result_resource_group, headers='keys', tablefmt='grid', floatfmt='.3f'))
    
    # Análise por ServiceName
    result_service_name, _ = analyze_costs(subscription_name, subscription_id, "ServiceName")
    print("\nCost analysis by ServiceName:")
    if isinstance(result_service_name, str):
        print("No Cost Found")
    else:
        print(tabulate(result_service_name, headers='keys', tablefmt='grid', floatfmt='.3f'))
