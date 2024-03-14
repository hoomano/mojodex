import os

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app import document_manager

from background_logger import BackgroundLogger
from jinja2 import Template



from app import llm, llm_conf


class WebsiteParser:
    logger_prefix = "WebsiteParser"

    MAX_WEBSITE_PAGES = 100

    website_chunk_validation_prompt = "/data/prompts/background/website_parser/is_website_chunk_relevant.txt"
    website_chunk_validator = llm(llm_conf, label="WEBSITE_CHUNK_VALIDATOR")

    def __init__(self):
        self.logger = BackgroundLogger(f"{WebsiteParser.logger_prefix}")

    def __get_all_page_urls(self, base_url):
        try:
            self.logger.debug(f"__get_all_page_urls: {base_url}")
            # Send a GET request to the base URL
            response = requests.get(base_url)

            # Create a BeautifulSoup object to parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all anchor tags (links) in the HTML
            anchor_tags = soup.find_all('a')

            # Extract the href attribute from each anchor tag and join it with the base URL
            page_urls = [urljoin(base_url, anchor.get('href'))
                         for anchor in anchor_tags]

            # Remove ending "/" from URLs
            page_urls = [
                url[:-1] if url.endswith('/') else url for url in page_urls]

            # Return the list of page URLs unique
            return list(set(page_urls))
        except Exception as e:
            raise Exception(f"__get_all_page_urls: {e}")

    def __get_webpage_text(self, url, retry=2):
        try:
            self.logger.debug(f"__get_webpage_text: {url}")
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            webpage_text = soup.text.strip()
            if webpage_text.strip() == "":
                if retry > 0:
                    self.logger.warning("🟠 Empty webpage text, retrying...")
                    return self.__get_webpage_text(url, retry - 1)
                else:
                    self.logger.warning("🔴 Empty webpage text, giving up...")
                    return None
            # remove multiple \n by only one
            webpage_text = "\n".join(
                [line for line in webpage_text.split("\n") if line.strip() != ""])

            return webpage_text
        except Exception as e:
            self.logger.error(f"__get_webpage_text: {e}")
            return None

    def website_to_doc(self, base_url, all_urls=False):
        try:
            self.logger.debug(f"website_to_doc: {base_url}")
            # Remove ending "/" from base_url
            if base_url[-1] == "/":
                base_url = base_url[:-1]
            all_page_urls = self.__get_all_page_urls(
                base_url) if all_urls else [base_url]
            self.logger.debug(
                f"website_to_doc: found {len(all_page_urls)} pages")
            text_list = []
            for link in all_page_urls[:WebsiteParser.MAX_WEBSITE_PAGES]:
                text = self.__get_webpage_text(link)
                if text is not None:
                    text_list.append({"link": link, "text": text})

            self.logger.debug(f"website_to_doc: Done")
            return text_list

        except Exception as e:
            raise Exception(f"website_to_doc: {e}")

    def __validate_website_chunk(self, chunk_text, user_id):
        try:
            with open(WebsiteParser.website_chunk_validation_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(
                    company_name=self.company_name, chunk_text=chunk_text)
            messages = [{"role": "user", "content": prompt}]

            responses = WebsiteParser.website_chunk_validator.invoke(
                messages, user_id, temperature=0, max_tokens=5)
            return responses[0].lower().strip() == "yes"
        except Exception as e:
            raise Exception(f"__validate_website_chunk: {e}")

    def update_website_document(self, user_id, base_url, document_pk, document_chunks_pks, company_name):
        try:
            # useful for validation
            self.company_name = company_name
            self.logger.debug(f"update_website: {base_url}")
            responses = self.website_to_doc(base_url, all_urls=False)
            document_manager.update_document(user_id, document_pk, document_chunks_pks, responses[0]["text"],
                                             chunk_validation_callback=self.__validate_website_chunk)

        except Exception as e:
            raise Exception(f"update_website: {e}")

    def create_website_document(self, user_id, base_url, company_name):
        try:
            self.company_name = company_name  # useful for validation
            self.logger.debug(f"update_website: {base_url}")
            responses = self.website_to_doc(base_url, all_urls=True)
            for response in responses:
                document_manager.new_document(user_id, response["text"], response["link"], document_type='webpage',
                                              chunk_validation_callback=self.__validate_website_chunk)
        except Exception as e:
            raise Exception(f"update_website: {e}")
