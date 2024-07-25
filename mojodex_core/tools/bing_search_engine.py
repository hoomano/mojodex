import os
import json
import requests

class BingSearchEngine:
    search_url = "https://api.bing.microsoft.com/v7.0/search" 

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BingSearchEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self.__class__._initialized:
            self.api_key = os.environ.get('BING_SEARCH_API_KEY')
            if not self.api_key:
                raise Exception("BING SEARCH API key not found")

    def search(self, query: str, n_results:int = 10):
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": n_results}
            response = requests.get(self.search_url, headers=headers, params=params)
            response.raise_for_status()
            search_results = response.json()
            return search_results
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: search :: {e}")
        
    def get_search_webpages_urls(self, query: str, n_results:int = 10):
        try:
            search_results = self.search(query, n_results)
            return [result['url'] for result in search_results['webPages']['value']]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_search_webpages_urls :: {e}")
