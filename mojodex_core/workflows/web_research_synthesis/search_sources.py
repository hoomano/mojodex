from typing import List
from mojodex_core.entities.workflow_step import WorkflowStep
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.tools.bing_search_engine import BingSearchEngine
from mojodex_core.workflows.web_research_synthesis.webpage import WebPage


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
