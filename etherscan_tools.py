import os
import requests
import logging
from langchain.agents import tool  # Import the @tool decorator

logging.basicConfig(level=logging.INFO)

# Global variables for API configuration
API_KEY = os.getenv('ETHERSCAN_API_KEY')
BASE_URL = "https://api.etherscan.io/api"

@tool
def get_recent_blocks(block_count: int = 10) -> list:
    """
    Fetches a list of recent block numbers. This is a placeholder implementation.
    
    Args:
        block_count (int): The number of recent blocks to fetch.
    
    Returns:
        list: A list of recent block numbers.
    """
    # Placeholder implementation, replace with actual logic to fetch block numbers
    return [12345678 - i for i in range(block_count)]

@tool
def get_block_transactions(block_number: int) -> list:
    """
    Fetches transactions for a given block number from the Etherscan API.
    
    Args:
        block_number (int): The block number to fetch transactions for.
    
    Returns:
        list: A list of transactions for the given block number.
    """
    params = {
        'module': 'proxy',
        'action': 'eth_getBlockByNumber',
        'tag': f"0x{block_number:x}",
        'boolean': 'true',
        'apikey': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        try:
            response_data = response.json()
            if 'result' in response_data and isinstance(response_data['result'], dict):
                return response_data['result'].get('transactions', [])
            else:
                logging.error(f"API request failed with response: {response.text}")
                return []
        except ValueError as e:
            logging.error(f"Error parsing JSON response: {e}")
            return []
    else:
        logging.error(f"API request failed with status code: {response.status_code}")
        return []

@tool
def get_whale_insights(block_count: int = 10, threshold: int = 1e18) -> str:
    """
    Provides a string summary of whale activities on the Ethereum blockchain by analyzing recent transactions.
    
    Args:
        block_count (int): The number of recent blocks to analyze.
        threshold (int): The value threshold (in wei) to classify a transaction as whale activity.
    
    Returns:
        str: A string summarizing whale activities detected in the recent blocks.
    """
    whale_activities = []
    for block_number in get_recent_blocks(block_count=block_count):
        transactions = get_block_transactions(block_number)
        for tx in transactions:
            if int(tx['value'], 16) >= threshold:
                whale_activities.append({'blockNumber': block_number, 'value': int(tx['value'], 16) / 1e18})
    
    if whale_activities:
        response = "Recent whale activities detected:\n"
        for activity in whale_activities:
            response += f"Block: {activity['blockNumber']}, Value: {activity['value']} ETH\n"
    else:
        response = "No significant whale activities detected in the recent blocks."
    return response