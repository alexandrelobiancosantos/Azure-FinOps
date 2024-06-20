# Azure Cost Analysis

Este projeto contém scripts para analisar os custos do Azure agrupados por diferentes critérios, como grupo ou tag. Ele utiliza a CLI do Azure para obter informações sobre as assinaturas e tokens de acesso, e faz requisições para a API de Gerenciamento de Custos do Azure para coletar e processar dados.

## Estrutura do Projeto

O projeto está organizado em vários módulos para melhorar a modularidade e a manutenção:

- **logging_utils.py**: Configurações de logging e manipulação de erros.
- **azure_cli_utils.py**: Funções para interagir com a CLI do Azure.
- **data_processing_utils.py**: Funções para processar dados e calcular métricas.
- **http_requests_utils.py**: Funções para fazer requisições HTTP para a API do Azure.
- **Report.py**: Script principal que executa a análise de custos.

## Instalação

1. Clone o repositório para o seu ambiente local:
    ```sh
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DO_REPOSITORIO>
    ```

2. Certifique-se de ter o Python instalado (versão 3.6+).

3. Instale as dependências necessárias:
    ```sh
    pip install -r requirements.txt
    ```

## Uso

### Report.py

O script principal `Report.py` é usado para analisar os custos do Azure. Abaixo está a descrição de como utilizá-lo.

#### Argumentos

- `subscription_prefix`: Prefixo da assinatura do Azure para analisar.
- `analysis_type`: Tipo de análise, podendo ser "grupo" ou "tag".
- `grouping_key`: Chave de agrupamento para a análise (e.g., ServiceName, Projeto).
- `--alert`: (Opcional) Ativa o modo de alerta para gerar alertas de altos custos.
- `--csv`: (Opcional) Salva os resultados em um arquivo CSV.
- `--date`: (Opcional) Data de início para o período de análise no formato YYYY-MM-DD.

#### Exemplos de Uso

1. Analisar custos por grupo:
    ```sh
    python Report.py <subscription_prefix> grupo <grouping_key> --date 2023-01-01 --csv
    ```

2. Analisar custos por tag com alertas:
    ```sh
    python Report.py <subscription_prefix> tag <tag_key> --alert --csv
    ```

## Módulos

### logging_utils.py

Configura o logging básico e manipula erros.

- `setup_logging()`: Configura o logging básico.
- `handle_errors(exception, message)`: Manipula erros logando a mensagem e a exceção, e encerra o programa.

### azure_cli_utils.py

Interage com a CLI do Azure para obter informações de assinaturas e tokens de acesso.

- `get_subscription_ids(subscription_prefix)`: Recupera IDs de assinaturas que começam com o prefixo dado.
- `get_access_token()`: Recupera um token de acesso para a API de gerenciamento do Azure.

### data_processing_utils.py

Processa dados e calcula métricas.

- `get_analysis_timeframe(start_date_str)`: Obtém o período de análise retroativo a sete dias a partir da data fornecida ou de ontem, se nenhuma data for fornecida.
- `check_alert(cost_yesterday, average_cost)`: Verifica se o custo de ontem excede o custo médio.
- `process_costs(costs_by_group, grouping_key, start_date, end_date, analysis_date_str)`: Processa os custos por grupo e calcula métricas.

### http_requests_utils.py

Faz requisições HTTP para a API de Gerenciamento de Custos do Azure e processa as respostas.

- `build_cost_management_request(subscription_id, grouping_type, grouping_name, access_token)`: Constrói a requisição para a API de Gerenciamento de Custos do Azure.
- `request_and_process(url, headers, payload, subscription_name)`: Envia a requisição para a API do Azure e processa a resposta.

## Contribuição

Se desejar contribuir com este projeto, por favor, siga os passos abaixo:

1. Faça um fork do repositório.
2. Crie uma nova branch (`git checkout -b feature/nova-feature`).
3. Faça suas alterações e comite-as (`git commit -am 'Adiciona nova feature'`).
4. Faça push para a branch (`git push origin feature/nova-feature`).
5. Abra um Pull Request.

