from lxml import html
from lxml.etree import tostring
from prompt.prompt import *
from chatGPT.api import chatgpt
from langchain_core.output_parsers import PydanticOutputParser
from model.response_model import NewsExtractWithXpath, UnwantedXpathExtract, Judgement
from common.utils import fetch_html, get_clean_text_from_html

fields = ['title', 'published_date', 'author', 'sapo', 'content']
mandatory_fields = ['title', 'published_date', 'content']

class XpathExtractor:
    def __init__(self, url, max_retries=2):
        self.url = url
        self.html_content = fetch_html(url)
        self.max_retries = max_retries

    def _extract(self):
        try:
            tree = html.fromstring(self.html_content)

            # Extract nội dung từ bài viết
            print("Extracting content...")
            parser = PydanticOutputParser(pydantic_object=NewsExtractWithXpath)
            format_instructions = parser.get_format_instructions()
            prompt = extract_prompt.format(html_content=self.html_content, format_instructions=format_instructions)
            response = chatgpt(prompt, system_prompt)
            response_dict = parser.invoke(response).dict()

            content_dict = {
                "title": get_clean_text_from_html(response_dict['title']),
                "published_date": get_clean_text_from_html(response_dict['published_date']),
                "author": get_clean_text_from_html(response_dict['author']),
                "sapo": get_clean_text_from_html(response_dict['sapo']),
                "content": get_clean_text_from_html(response_dict['content']),
            }
            xpath_dict = {
                "title_xpath": response_dict['title_xpath'],
                "published_date_xpath": response_dict['published_date_xpath'],
                "author_xpath": response_dict['author_xpath'],
                "sapo_xpath": response_dict['sapo_xpath'],
                "content_xpath": response_dict['content_xpath'],
            }

            # Extract xpath của các thẻ chứa quảng cáo, bài viết liên quan
            content_html = tostring(tree.xpath(xpath_dict['content_xpath'])[0], encoding='unicode')

            parser = PydanticOutputParser(pydantic_object=UnwantedXpathExtract)
            format_instructions = parser.get_format_instructions()
            prompt = extract_unwanted_prompt.format(content=content_dict['content'], content_html=content_html, format_instructions=format_instructions)
            response = chatgpt(prompt, system_prompt)
            response_dict = parser.invoke(response).dict()

            unwanted_xpath = [xpath_dict['content_xpath'] + xpath for xpath in response_dict['unwanted_xpath']]
            xpath_dict['unwanted_xpath'] = unwanted_xpath

            for xpath in xpath_dict['unwanted_xpath']:
                elements_to_remove = tree.xpath(xpath)
                if elements_to_remove is not None:
                    for element in elements_to_remove:
                        element.getparent().remove(element)

            for field in fields:
                if xpath_dict[f"{field}_xpath"] == '' or tree.xpath(xpath_dict[f"{field}_xpath"]) is None:
                    if field in mandatory_fields:
                        return None, None
                    xpath_dict[f"{field}_xpath"] = ''

            print("EXTRACTING DONE")
            print("Content_dict:")
            print(content_dict)
            print("Xpath_dict:")
            print(xpath_dict)

            return content_dict, xpath_dict
        except Exception as e:
            print(f"Extract xpath failed: {e}")
            return None, None

    def execute_xpath(self, xpath_dict):
        try:
            tree = html.fromstring(self.html_content)
            # Remove unwanted elements
            for xpath in xpath_dict['unwanted_xpath']:
                elements_to_remove = tree.xpath(xpath)
                if elements_to_remove is not None:
                    for element in elements_to_remove:
                        element.getparent().remove(element)
            print("Removing unwanted elements done")
            content_dict = {}
            content_dict["title"] = tostring(tree.xpath(xpath_dict['title_xpath'])[0], encoding='unicode')
            print("Extract title done")
            content_dict["published_date"] = tostring(tree.xpath(xpath_dict['published_date_xpath'])[0], encoding='unicode')
            print("Extract published date done")
            content_dict["author"] = tostring(tree.xpath(xpath_dict['author_xpath'])[0], encoding='unicode') if xpath_dict['author_xpath'] != '' else ''
            print("Extract author done")
            content_dict["sapo"] = tostring(tree.xpath(xpath_dict['sapo_xpath'])[0], encoding='unicode') if xpath_dict['sapo_xpath'] != '' else ''
            print("Extract sapo done")
            sapo_element = tree.xpath(xpath_dict['sapo_xpath'])
            if sapo_element is not None:
                for element in sapo_element:
                    element.getparent().remove(element)

            content_dict['content'] = tostring(tree.xpath(xpath_dict['content_xpath'])[0], encoding='unicode')
            print("Extract content done")
            return content_dict
        except Exception as e:
            print(f"Execute xpath failed: {e}")
            return None

    def validate_with_content(self, content_dict, xpath_dict):
        if content_dict is None or xpath_dict is None:
            return False
        try:
            extracted_content_dict = self.execute_xpath(xpath_dict)
            if extracted_content_dict is None:
                return False

            for field in fields:
                print('-' * 50)
                print(f"Validating {field}...")
                cleaned_text = get_clean_text_from_html(extracted_content_dict[field])
                if cleaned_text == '':
                    if field in mandatory_fields:
                        print(f"Extracted {field}:\n{cleaned_text}")
                        print("UNMATCHED")
                        print('-' * 50)
                        return False
                    print("IGNORED")
                    print('-' * 50)
                    continue
                parser = PydanticOutputParser(pydantic_object=Judgement)
                format_instructions = parser.get_format_instructions()
                prompt = judgement_prompt.format(
                    format_instructions=format_instructions,
                    expected_value=content_dict[field],
                    extracted_value=cleaned_text
                )
                response = chatgpt(prompt, temperature=0.3)
                response_dict = parser.invoke(response).dict()
                print(f"Extracted {field}:\n{cleaned_text}")
                print(f"Expected {field}:\n{content_dict[field]}")
                print(f"Thought: {response_dict['thought']}")
                if not response_dict['judgement']:
                    print("UNMATCHED")
                    print('-' * 50)
                    return False
                print("MATCHED")
                print('-' * 50)
            return True

        except Exception as e:
            print(f"Validate xpath failed: {e}")
            return False

    def extract(self):
        retry_counter = 0
        content_dict = None
        xpath_dict = None
        print("MAX RETRIES: ", self.max_retries)
        print("="*50)

        while retry_counter <= self.max_retries:
            print(f"ATTEMPT: {retry_counter}...")
            content_dict, xpath_dict = self._extract()
            if self.validate_with_content(content_dict, xpath_dict):
                break
            retry_counter += 1
        if retry_counter > self.max_retries:
            print("EXTRACT FAILED")
            return None, None
        content_dict = self.execute_xpath(xpath_dict)

        return content_dict, xpath_dict
