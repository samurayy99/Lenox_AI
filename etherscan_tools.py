import os
import requests
import requests
from langchain.agents import tool  # Use the @tool decorator

class EtherscanTool:
    """
    A tool for interacting with the Etherscan API to fetch blockchain data.
    
    Attributes:
        api_key (str): The API key used for authenticating with the Etherscan API.
        base_url (str): The base URL for the Etherscan API.
    """
    def __init__(self, api_key):
        """
        Initializes the EtherscanTool with an API key.
        
        Args:
            api_key (str): The API key for Etherscan.
        """
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"

    def get_recent_blocks(self, block_count):
        """
        Fetches a list of recent block numbers. This is a placeholder implementation.
        
        Args:
            block_count (int): The number of recent blocks to fetch.
        
        Returns:
            list: A list of recent block numbers.
        """
        return [12345678 - i for i in range(block_count)]

    def get_block_transactions(self, block_number):
        """
        Fetches transactions for a given block number from the Etherscan API.
        
        Args:
            block_number (int): The block number to fetch transactions for.
        
        Returns:
            list: A list of transactions for the given block number, if the request is successful. Otherwise, returns an empty list.
        """
        params = {
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block_number),
            'boolean': 'true',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'result' in response_data and isinstance(response_data['result'], dict):
                    return response_data['result'].get('transactions', [])
                else:
                    logging.error(f"API-Anfrage fehlgeschlagen mit Status-Code: {response.status_code} und Antwort: {response.text}")
                    return []
            except ValueError as e:
                logging.error(f"Fehler beim Parsen der JSON-Antwort: {e}")
                return []
        else:
            logging.error(f"API-Anfrage fehlgeschlagen mit Status-Code: {response.status_code} und Antwort: {response.text}")
            return []
    
    
    def get_whale_insights(self, block_count: int = 10, threshold: int = 1e18) -> dict:
        """
        Provides insights into whale activities on the Ethereum blockchain by analyzing recent transactions.
        
        Args:
            block_count (int): The number of recent blocks to analyze.
            threshold (int): The value threshold (in wei) to classify a transaction as whale activity.
        
        Returns:
            dict: A dictionary containing information about whale activities, including the block number and value of transactions that meet the threshold.
        """
        whale_activities = []
        for block_number in self.get_recent_blocks(block_count):
            transactions = self.get_block_transactions(block_number)
            for tx in transactions:
                if int(tx['value'], 16) >= threshold:
                    whale_activities.append({'blockNumber': block_number, 'value': int(tx['value'], 16) / 1e18})
        return {'whale_activities': whale_activities}

# Instantiate the EtherscanTool with the API key
etherscan_tool = EtherscanTool(api_key=os.getenv('ETHERSCAN_API_KEY'))

@tool
def get_whale_insights(block_count: int = 10, threshold: int = 1e18) -> str:
    """
    A decorated function that provides a string summary of whale activities on the Ethereum blockchain.
    
    This function utilizes the EtherscanTool to fetch and analyze blockchain transactions.
    
    Parameters:
        block_count (int): The number of recent blocks to analyze.
        threshold (int): The value threshold to classify a transaction as whale activity.
    
    Returns:
        str: A string summarizing whale activities detected in the recent blocks.
    """
    insights = etherscan_tool.get_whale_insights(block_count, threshold)
    
    if insights and 'whale_activities' in insights:
        response = "Recent whale activities detected:\n"
        for activity in insights['whale_activities']:
            response += f"Block: {activity['blockNumber']}, Value: {activity['value']} ETH\n"
    else:
        response = "No significant whale activities detected in the recent blocks."
    return response