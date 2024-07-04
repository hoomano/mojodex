import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from mojodex_core.db import with_db_session
from mojodex_core.documents.document_manager import DocumentManager
from mojodex_core.entities.db_base_entities import MdCompany, MdDocument, MdUser
from mojodex_core.entities.document import Document
from mojodex_core.llm_engine.mpt import MPT


class WebsiteParser:
    logger_prefix = "WebsiteParser"

    MAX_WEBSITE_PAGES = 100

    website_chunk_validation_mpt_filename = "instructions/is_website_chunk_relevant.mpt"

    def __get_all_page_urls(self, base_url):
        try:
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
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            webpage_text = soup.text.strip()
            if webpage_text.strip() == "":
                if retry > 0:
                    return self.__get_webpage_text(url, retry - 1)
                else:
                    return None
            # remove multiple \n by only one
            webpage_text = "\n".join(
                [line for line in webpage_text.split("\n") if line.strip() != ""])

            return webpage_text
        except Exception as e:
            return None

    def website_to_doc(self, base_url, all_urls=False):
        try:
            # Remove ending "/" from base_url
            if base_url[-1] == "/":
                base_url = base_url[:-1]
            all_page_urls = self.__get_all_page_urls(
                base_url) if all_urls else [base_url]
            text_list = []
            for link in all_page_urls[:WebsiteParser.MAX_WEBSITE_PAGES]:
                text = self.__get_webpage_text(link)
                if text is not None:
                    text_list.append({"link": link, "text": text})

            return text_list

        except Exception as e:
            raise Exception(f"website_to_doc: {e}")

    def __validate_website_chunk(self, chunk_text, user_id):
        try:
            website_chunk_validation = MPT(
                WebsiteParser.website_chunk_validation_mpt_filename, company_name=self.company_name, chunk_text=chunk_text)

            responses = website_chunk_validation.run(
                user_id=user_id, temperature=0, max_tokens=5)
            return responses[0].lower().strip() == "yes"
        except Exception as e:
            raise Exception(f"__validate_website_chunk: {e}")

    @with_db_session
    def update_website_document(self, document_pk, db_session):
        try:
            document: Document = db_session.query(Document).filter(Document.document_pk == document_pk).first()
                  
            company_name =db_session.query(MdCompany.name) \
            .join(MdUser, MdUser.company_fk == MdCompany.company_pk) \
            .join(MdDocument, MdDocument.author_user_id == MdUser.user_id) \
            .filter(MdDocument.document_pk == document_pk) \
            .first()[0]
            # useful for validation
            self.company_name = company_name
            responses = self.website_to_doc(document.name, all_urls=False)
            document.update(responses[0]["text"], chunk_validation_callback=self.__validate_website_chunk)
        except Exception as e:
            raise Exception(f"update_website: {e}")

    def create_website_document(self, user_id, base_url, company_name):
        try:
            self.company_name = company_name  # useful for validation
            responses = self.website_to_doc(base_url, all_urls=True)
            for response in responses:
                DocumentManager().new_document(user_id, response["text"], response["link"], document_type='webpage',
                                              chunk_validation_callback=self.__validate_website_chunk)
        except Exception as e:
            raise Exception(f"update_website: {e}")
