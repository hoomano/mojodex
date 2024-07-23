
import json
from typing import List

from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT
import requests
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
class WebPage:

    def __init__(self, url):
        self.url = url
        self._scrapped_text = None

    @property
    def scrapped_text(self):
        return self._scrapped_text

    
    def scrap_to_get_text(self):
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                # go to url
                page.goto(self.url)

                try:
                    # Wait for the network to be idle with a timeout
                    # To ensure that the page is fully loaded
                    page.wait_for_load_state('networkidle', timeout=20000)  # Wait up to 20 seconds
                except TimeoutError:
                    return None

                # get HTML
                html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            webpage_text = soup.text.strip()
            if webpage_text.strip() == "":
                return None
            # remove multiple \n by only one
            webpage_text = "\n".join(
                [line for line in webpage_text.split("\n") if line.strip() != ""])
            self._scrapped_text = webpage_text
            return webpage_text
        except Exception as e:
            return None
        
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
            search_results = self.search(query)
            with open('/data/search_results.json', 'w') as f:
                json.dump(search_results, f, indent=4)
            return [result['url'] for result in search_results['webPages']['value']]
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_search_webpages_urls :: {e}")

class SearchSourcesStep(WorkflowStep):

    create_note_from_webpage_mpt_filename = "mojodex_core/workflows/web_research_synthesis/create_note_from_webpage.mpt"
    ask_for_another_search_mpt_filename = "mojodex_core/workflows/web_research_synthesis/ask_for_another_search.mpt"

    def _search(self, query: str, already_parsed_links: set, user_id, user_task_execution_pk, task_name_for_system):
        try:
            webpages_urls = BingSearchEngine().get_search_webpages_urls(query, n_results=5)
            for url in webpages_urls:
                if url not in already_parsed_links:
                    already_parsed_links.add(url)
                    webpage = WebPage(url)
                    webpage_text = webpage.scrap_to_get_text()
                    if webpage_text:
                        try:
                            webpage_note = self._create_note_from_webpage_text(query, webpage_text, user_id, user_task_execution_pk, task_name_for_system)
                            return {'query': query, 'link': url, 'note': webpage_note}, already_parsed_links
                        except Exception as e:
                            # This can happened for example if the webpage is too long for LLM context. Just move on to the next link.
                            print(f"🔴 Error creating webpage note: {e}")
                    
            return {'query': query, 'link': None, 'note': None}, already_parsed_links
        except Exception as e:
            raise Exception(f"_search :: {e}")
        
    def _create_note_from_webpage_text(self, query: str, webpage_text: str, user_id, user_task_execution_pk, task_name_for_system):
        try:
            create_note_mpt = MPT(self.create_note_from_webpage_mpt_filename,
                                  query=query, webpage_text=webpage_text)
            with open('/data/create_note_prompt.txt', 'w') as f:
                f.write(create_note_mpt.prompt)
            note = create_note_mpt.run(user_id=user_id, temperature=0, max_tokens=4000,
                                                user_task_execution_pk=user_task_execution_pk,
                                                task_name_for_system=task_name_for_system)
            return note
        except Exception as e:
            raise Exception(f"_create_note_from_webpage_text :: {e}")
        
    def _call_llm_for_another_search(self, research_subject, sources, user_id, user_task_execution_pk, task_name_for_system):
        try:
            # MPT call
            another_search_mpt = MPT(self.ask_for_another_search_mpt_filename,
                                     research_subject=research_subject, sources=sources)
            with open('/data/another_query_prompt.txt', 'w') as f:
                f.write(another_search_mpt.prompt)
            query = another_search_mpt.run(user_id=user_id, temperature=0, max_tokens=4000,
                                             user_task_execution_pk=user_task_execution_pk,
                                             task_name_for_system=task_name_for_system)
            query = query.strip()
            
            print(f"🔵 Another search query: {query}")
            return query if query != "None" else None
        except Exception as e:
            raise Exception(f"_call_llm_for_another_search :: {e}")

   
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, past_validated_steps_results: List[dict], user_id: str, user_task_execution_pk: int, task_name_for_system: str, session_id:str):
        try: 
            print(f"🟢 parameter: {parameter}")
            research_subject = parameter['research_subject']

            n_max_searches = 3
            already_parsed_links = set() # To avoid parsing the same link twice
            sources = [] #{'query': '', 'link':'', 'note':''}

            query = research_subject 

            while query:
                source, already_parsed_links = self._search(query, already_parsed_links, user_id, user_task_execution_pk, task_name_for_system)
                print(f"🟣 Source: {source['link']}")
                sources.append(source)
                if len(sources) < n_max_searches:
                    # ASK THE LLM IF IT WANT TO MAKE ANOTHER SEARCH
                    query = self._call_llm_for_another_search(research_subject, sources, user_id, user_task_execution_pk, task_name_for_system)
                else:
                    query = None

            sources_notes = ""
            sources_urls = ""
            for source in sources:
                if source['note']:
                    sources_notes += f"\n\n{source['note']}"
                    sources_urls += f"\n{source['link']}"
            
            return [{'notes': sources_notes, 'sources_urls': sources_urls}]
        
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: execute :: {e}")
