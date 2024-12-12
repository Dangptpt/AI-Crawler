from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from common.utils import fetch_html
from model.response_model import SeedXpath
from chatGPT.api import chatgpt
from lxml import html

system_message = "Bạn là một nhà báo chuyên nghiệp chuyên trích xuất thông tin từ các trang tin tức."


class SeedExtractor:
    def __init__(self, url):
        self.url = url
        self.html_content = fetch_html(url)

    def get_seed_xpath(self):
        try:
            parser = PydanticOutputParser(pydantic_object=SeedXpath)
            query = (f"""Dưới đây là html một trang web chứa danh sách các tin tức. Bạn hãy trích xuất xpath đến href chứa url của các tin tức nằm trong trang danh sách trên.
                        {self.html_content}
                        {parser.get_format_instructions()}""")

            response = chatgpt(query, system_message)
            response_dict = parser.invoke(response).dict()
            return response_dict['news_url_xpath']
        except:
            return None

    def get_seed_url_list(self, seed_xpath=None):
        try:
            if seed_xpath is None:
                seed_xpath = self.get_seed_xpath()
            if seed_xpath is None:
                return None
            tree = html.fromstring(self.html_content)
            hrefs = tree.xpath(seed_xpath)
            return hrefs
        except:
            return None
