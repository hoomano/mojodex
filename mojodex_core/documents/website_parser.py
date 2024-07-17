import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from mojodex_core.documents.document_service import DocumentService
from mojodex_core.embedder.embedding_service import EmbeddingService
from mojodex_core.entities.document import Document
from mojodex_core.llm_engine.mpt import MPT


class WebsiteParser:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WebsiteParser, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    # Maximum number of pages to parse from a website
    MAX_WEBSITE_PAGES = 100

    website_chunk_validation_mpt_filename = "mojodex_core/instructions/is_website_chunk_relevant.mpt"
    

    def check_url_validity(self, website_url):
        """
        Return valid url if website_url is valid or have been corrected, raises exception otherwise
        :param website_url: the url to check
        :return: valid url
        """
        try:
            if not website_url.startswith("https://") and not website_url.startswith("http://"):
                website_url = "https://" + website_url
            response = requests.get(website_url)
            return website_url
        except Exception as e:
            raise Exception(f"invalid_url")

    def get_webpage_text(self, url, retry=2):
        """
        Retrieve the text content of a webpage
        """
        try:
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            webpage_text = soup.text.strip()
            if webpage_text.strip() == "":
                if retry > 0:
                    return self.get_webpage_text(url, retry - 1)
                else:
                    return None
            # remove multiple \n by only one
            webpage_text = "\n".join(
                [line for line in webpage_text.split("\n") if line.strip() != ""])

            return webpage_text
        except Exception as e:
            return None
        
    def _get_all_page_urls(self, base_url):
        """
        Retrieve all page URLs from a website
        """
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

    def _extract_text_of_pages_from_website(self, base_url):
        """
        Retrieve the text content of multiple pages from a website
        """
        try:
            # Remove ending "/" from base_url
            if base_url[-1] == "/":
                base_url = base_url[:-1]
            all_page_urls = self._get_all_page_urls(base_url)
            text_list = []
            for link in all_page_urls[:WebsiteParser.MAX_WEBSITE_PAGES]:
                text = self.get_webpage_text(link)
                if text is not None:
                    text_list.append({"link": link, "text": text})

            return text_list

        except Exception as e:
            raise Exception(f"_extract_text_of_pages_from_website: {e}")
        

    def _validate_website_chunk(self, chunk_text, user_id):
        """
        Decides whether or not the chunk of a website text is relevant and should be stored.

        A relevant chunk is a chunk that will be useful to help the user with their tasks.
        Any chunk containing information about the company's products, services, terms, conditions, information, etc. is relevant.
        Only chunk containing footers, headers, menus, etc. are not relevant.
        """
        try:
            website_chunk_validation = MPT(
                WebsiteParser.website_chunk_validation_mpt_filename, chunk_text=chunk_text)
            response = website_chunk_validation.run(
                user_id=user_id, temperature=0, max_tokens=5)
            return response.lower().strip() == "yes"
        except Exception as e:
            raise Exception(f"__validate_website_chunk: {e}")
    

    def create_document_from_website(self, user_id, base_url):
        """
        Turn website into a Mojodex Document
        """
        try:
            responses = self._extract_text_of_pages_from_website(base_url)
            for response in responses:
                DocumentService().new_document(user_id, response["text"], response["link"], document_type='webpage',
                                              chunk_validation_callback=self._validate_website_chunk)
        except Exception as e:
            raise Exception(f"update_website: {e}")
        
    
    def update_webpage_document(self, document: Document):
        try:
            new_text = self.get_webpage_text(document.name)
            document.update(new_text, chunk_validation_callback=self._validate_website_chunk)
        except Exception as e:
            raise Exception(f"update_website: {e}")
        

    