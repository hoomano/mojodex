import json
import os
from IPython.utils import io
from jinja2 import Template
from serpapi import GoogleSearch
import requests
from bs4 import BeautifulSoup

from background_logger import BackgroundLogger
from models.task_tool_execution.tools.tool import Tool
from mojodex_core.costs_manager.serp_api_costs_manager import SerpAPICostsManager

from app import llm, llm_conf



class GoogleSearchTool(Tool):
    logger_prefix = "GoogleSearchTool ::"

    name = "google_search"
    tool_specifications = """{
         "query": <query you want to search on Google. It has to be really short, mainly keywords and precise. Only one information to search.>,
         "gl":<Country to use for the Google search. Two-letter country code>,
         "hl":<Language to use for the Google search. Two-letter language code.>
        }"""
    n_total_usages = 3

    scrapper_prompt = "/data/prompts/background/task_tool_execution/google_search/scrapper_prompt.txt"
    scrapper = llm(llm_conf, label="WEB_SCRAPPER")
    
    serp_api_costs_manager = SerpAPICostsManager()

    def __init__(self, user_id, task_tool_execution_pk, user_task_execution_pk, task_name_for_system, **kwargs):
        try:
            if "SERPAPI_KEY" not in os.environ:
                raise Exception("SERPAPI_KEY is not defined")
            self.logger = BackgroundLogger(f"{GoogleSearchTool.logger_prefix}")
            self.logger.debug(f"__init__")
            super().__init__(GoogleSearchTool.name, GoogleSearchTool.tool_specifications, task_tool_execution_pk,
                             self.logger, user_id, user_task_execution_pk, task_name_for_system, self.n_total_usages)
        except Exception as e:
            raise Exception(f"GoogleSearchTool : __init__ :: {e}")

    def run_tool(self, json_params, tool_execution_context, usage_description, knowledge_collector):
        try:
            self.logger.debug(f"run_tool with params {json_params}")
            query = json_params["query"]
            gl = json_params["gl"]
            hl = json_params["hl"]
            results = []
            result = None
            self.logger.debug(f"run_tool :: query {query}")
            try:
                web_search_result = self.__serp_api(query, num=5, gl=gl, hl=hl)
            except Exception as e:
                self.logger.error(f"run_tool :: {e}")
                web_search_result = None

            if web_search_result is None:
                return None
            if not isinstance(web_search_result, str):
                index = 0
                while index < len(web_search_result):
                    web_search_result_index = web_search_result[index]
                    if "link" in web_search_result_index:
                        url = web_search_result_index["link"]
                        scrap_result = None
                        scrapped = False
                        try:
                            if not url.endswith(
                                    ".pdf") and not '/download/' in url:  # ignore pdf or download files that are usually too long and summarizer is not working
                                scrap_result = self.__scrap(url, query)
                                scrapped = True
                            else:
                                scrap_result = None
                        except Exception as e:
                            self.logger.error(f"run_tool :: {e}")
                        if scrap_result:
                            result = {"source": url, "extracted": scrap_result}
                        elif scrapped:
                            result = {"source": url,
                                      "extracted": "No good search result found"}
                        results.append(result)
                    index += 1
            return results
        except Exception as e:
            raise Exception(f"activate :: {e}")

    def __serp_api(self, query, num=1, gl="us", hl="en"):
        try:
            params = {
                "api_key": os.getenv("SERPAPI_KEY"),
                "engine": "google",
                "q": query.strip(),
                "google_domain": "google.com",
                "gl": gl,  # Google Country
                "hl": hl,  # Google UI Language
                "num": num
            }
            with io.capture_output() as captured:  # disables prints from GoogleSearch
                search = GoogleSearch(params)
                res = search.get_dict()
            self.serp_api_costs_manager.on_search(user_id=self.user_id, num_of_results_asked=num,
                                             user_task_execution_pk=self.user_task_execution_pk,
                                             task_name_for_system=self.task_name_for_system)
            if "error" in res.keys():
                raise ValueError(f"Got error from SerpAPI: {res['error']}")
            if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
                toret = res["answer_box"]["answer"]
            elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
                toret = res["answer_box"]["snippet"]
            elif "answer_box" in res.keys() and "snippet_highlighted_words" in res["answer_box"].keys():
                toret = res["answer_box"]["snippet_highlighted_words"][0]
            elif "sports_results" in res.keys() and "game_spotlight" in res["sports_results"].keys():
                toret = res["sports_results"]["game_spotlight"]
            elif "shopping_results" in res.keys() and "title" in res["shopping_results"][0].keys():
                toret = res["shopping_results"][:3]
            elif "knowledge_graph" in res.keys() and "description" in res["knowledge_graph"].keys():
                toret = res["knowledge_graph"]["description"]
            elif "organic_results" in res.keys():
                toret = []
                for organic_result in res["organic_results"]:
                    result = {}
                    if "title" in organic_result.keys():
                        result["title"] = organic_result["title"]
                    if "snippet" in organic_result.keys():
                        result["snippet"] = organic_result["snippet"]
                    if "link" in organic_result.keys():
                        result["link"] = organic_result["link"]
                    toret.append(result)
            else:
                toret = []
            return toret
        except Exception as e:
            raise Exception(f"__serp_api: {e}")

    def __scrap(self, url, query):
        try:
            self.logger.debug(f"__scrap : {url}")
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # if there is a "main" meta tag, use its content attribute
            main_content = soup.find("main")
            text_content = main_content.text if main_content else soup.text

            # call gpt4
            with open(GoogleSearchTool.scrapper_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(
                    url=url, text_content=text_content, search=query)

            messages = [{"role": "user", "content": prompt}]

            responses = GoogleSearchTool.scrapper.invoke(messages, self.user_id,
                                                       temperature=0, max_tokens=1000,
                                                       user_task_execution_pk=self.user_task_execution_pk,
                                                       task_name_for_system=self.task_name_for_system,
                                                       )

            response = responses[0].strip()
            if response.lower().strip() == "none":
                return None
            return response
        except Exception as e:
            raise Exception(f"__scrap: {e}")
