import requests
from bs4 import BeautifulSoup
from jinja2 import Template


from mojodex_backend_logger import MojodexBackendLogger

from app import llm, llm_conf, llm_backup_conf

from mojodex_core.json_loader import json_decode_retry
from app import on_json_error
from mojodex_core.llm_engine.mpt import MPT


class WebsiteParser:
    logger_prefix = "WebsiteParser"

    extract_website_info_mpt_filename = "instructions/extract_infos_from_webpage.mpt"

    website_info_extractor = llm(llm_conf, label="EXTRACT_COMPANY_INFO_FROM_WEBSITE",
                                 llm_backup_conf=llm_backup_conf)

    def __init__(self):
        self.logger = MojodexBackendLogger(f"{WebsiteParser.logger_prefix}")

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

    def __get_webpage_text(self, url, retry=2):

        self.logger.debug(f"__get_webpage_text: {url}")
        response = requests.get(url)

        try:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            webpage_text = soup.text.strip()
            if webpage_text.strip() == "":
                if retry > 0:
                    self.logger.debug("🟠 Empty webpage text, retrying...")
                    return self.__get_webpage_text(url, retry - 1)
                else:
                    raise Exception("🔴 Empty webpage text, giving up...")
            # remove multiple \n by only one
            webpage_text = "\n".join(
                [line for line in webpage_text.split("\n") if line.strip() != ""])

            return webpage_text
        except Exception as e:
            raise Exception(f"__get_webpage_text: {e}")

    @json_decode_retry(retries=3, required_keys=["name", "description", "emoji"], on_json_error=on_json_error)
    def __scrap_webpage(self, user_id, website_url, webpage_text):
        try:
            website_info_mpt = MPT(WebsiteParser.extract_website_info_mpt_filename, url=website_url, text_content=webpage_text)

            responses = WebsiteParser.website_info_extractor.invoke_from_mpt(website_info_mpt, user_id,
                                                                  temperature=0, max_tokens=1000,
                                                                  json_format=True)[0]

            return responses
        except Exception as e:
            raise Exception(f"__scrap_webpage: {e}")

    def get_company_name_and_description(self, user_id, website_url):
        try:
            self.logger.debug(
                f"get_company_name_and_description: {website_url}")
            webpage_text = self.__get_webpage_text(website_url)
            self.logger.debug("Get webpage text")
            infos = self.__scrap_webpage(user_id, website_url, webpage_text)
            self.logger.debug(f"Scrap webpage - infos : {infos}")
            name, description, emoji = infos["name"], infos["description"], infos["emoji"]
            return name, description, emoji
        except Exception as e:
            raise Exception(f"get_company_name_and_description: {e}")
