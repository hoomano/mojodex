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
        