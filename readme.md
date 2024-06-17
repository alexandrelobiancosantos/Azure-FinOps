# FinOps Cost Analysis

## Overview

This project provides tools to analyze Azure cost management by different dimensions such as `ServiceName`, `ResourceGroup`, `MeterCategory`, and `TagKey`. The scripts help in monitoring and managing cloud expenditure effectively.

## Scripts

- **costAnalysisBy.py**: Analyzes Azure costs by dimensions like `ServiceName`, `ResourceGroup`, and `MeterCategory`.
- **costAnalysisByTag.py**: Analyzes Azure costs grouped by tag values, specifically useful for tracking project-related expenses.

## Prerequisites

Ensure you have the following roles assigned to run the scripts:

- **Cost Management Contributor**: To read cost data.
- **Reader**: To read resources and tags.

## Setup

1. **Open the Integrated Terminal**

    Open the integrated terminal in your browser environment where you have access to Azure CLI.

<<<<<<< HEAD


=======
>>>>>>> 457488cdb0a40d663917d790a771bfdebc7d4861
2. **Install Azure CLI**

    Ensure you have [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and configured.

<<<<<<< HEAD
3. **Assign Roles**
=======
3. **Login to Azure**

    ```sh
    az login
    ```

4. **Assign Roles**
>>>>>>> 457488cdb0a40d663917d790a771bfdebc7d4861

    Ensure your account has the necessary roles:

    ```sh
    az role assignment create --role "Cost Management Contributor" --assignee <your_account>
    az role assignment create --role "Reader" --assignee <your_account>
    ```

## Usage

### costAnalysisBy.py

Analyze Azure costs by dimensions like `ServiceName`, `ResourceGroup`, and `MeterCategory`.

**Syntax:**


python costAnalysisBy.py <Dimension> <Subscription_Prefix>


### costAnalysisByTag.py

Analyze Azure costs grouped by tag values.


**Syntax:**

python costAnalysisByTag.py <Tag_Key> <Subscription_Prefix>

<<<<<<< HEAD
## Output
The scripts output a detailed cost analysis in tabular format, showing average cost, cost for the previous day, and alerts if costs exceed the average plus standard deviation.

## Anomaly Detection
The scripts include a simple anomaly detection mechanism where an alert is triggered if the cost for the previous day exceeds the average cost plus one standard deviation for the period analyzed. Because who doesn’t love a good surprise?


## Example Output
=======
### Output
The scripts output a detailed cost analysis in tabular format, showing average cost, cost for the previous day, and alerts if costs exceed the average plus standard deviation.

### Anomaly Detection
The scripts include a simple anomaly detection mechanism where an alert is triggered if the cost for the previous day exceeds the average cost plus one standard deviation for the period analyzed. Because who doesn’t love a good surprise?


### Example Output
>>>>>>> 457488cdb0a40d663917d790a771bfdebc7d4861

costAnalysisByTag.py
INFO:root:Starting analysis for tag key: projeto and subscription prefix: LOBIANCO - NPROD
INFO:root:Access token generated successfully.
INFO:root:Analyzing subscription: LOBIANCO - NPROD with ID: <subscription_id>
INFO:root:Total Cost Yesterday: R$ 0.052
INFO:root:Cost analysis by tag key 'projeto':
+----+---------------+----------------+------------------+---------+---------------------------------+-----------------+
|    | projeto       |   Average Cost |   Cost Yesterday | Alert   | Period of Average Calculation   | Analysis Date   |
+====+===============+================+==================+=========+=================================+=================+
|  0 | python_finops |          0.035 |            0.052 | Yes     | 2024-06-07 to 2024-06-14        | 2024-06-14      |
+----+---------------+----------------+------------------+---------+---------------------------------+-----------------+


### Conclusion
This project helps in managing and optimizing Azure costs by providing detailed cost analysis through easy-to-use scripts. Ensure you have the necessary Azure roles assigned and follow the setup instructions for seamless execution.