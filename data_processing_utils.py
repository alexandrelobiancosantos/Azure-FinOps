import statistics
import pandas as pd
from datetime import datetime, timedelta
from .logging_utils import handle_errors

def get_analysis_timeframe(start_date_str=None):
    """
    Get the analysis timeframe retroactive to seven days from the given date or yesterday if no date is given.
    
    Args:
        start_date_str (str, optional): The start date in 'YYYY-MM-DD' format. Defaults to None.

    Returns:
        tuple: Start date, end date, and timeframe dictionary.
    """
    if start_date_str:
        end_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.utcnow() - timedelta(days=1)
    
    start_date = end_date - timedelta(days=7)
    
    timeframe = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d')
    }
    return start_date, end_date, timeframe

def check_alert(cost_yesterday, average_cost):
    """
    Check if the cost for yesterday exceeds the average cost.
    Returns:
        str: "Yes" if cost_yesterday exceeds average_cost, otherwise "No".
    """
    return "Yes" if cost_yesterday > average_cost else "No"

def process_costs(costs_by_group, grouping_key, start_date, end_date, analysis_date_str):
    """
    Process costs by group and calculate average costs, alerts, and additional metrics.

    Args:
        costs_by_group (dict): The costs grouped by a specific key.
        grouping_key (str): The key to group costs by.
        start_date (datetime): The start date for the analysis period.
        end_date (datetime): The end date for the analysis period.
        analysis_date_str (str): The string representation of the analysis date.

    Returns:
        list: List of results with average costs, alerts, and additional metrics.
    """
    results = []

    for group_value, costs in costs_by_group.items():
        cost_values = [cost for date, cost in costs]
        average_cost = statistics.mean(cost_values)
        cost_on_analysis_date = next((cost for date, cost in costs if date == int(analysis_date_str)), 0)
        alert = check_alert(cost_on_analysis_date, average_cost)
        percent_variation = ((cost_on_analysis_date - average_cost) / average_cost) * 100 if average_cost != 0 else 0
        cost_difference = cost_on_analysis_date - average_cost

        results.append({
            grouping_key: group_value,
            "Average Cost": average_cost,
            "Analysis Date Cost": cost_on_analysis_date,
            "Alert": alert,
            "Percent Variation": percent_variation,
            "Cost Difference": cost_difference,
            "Period of Average Calculation": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "Analysis Date": end_date.strftime('%Y-%m-%d')
        })

    return results
