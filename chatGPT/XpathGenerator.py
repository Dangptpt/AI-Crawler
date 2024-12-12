from lxml import html
from lxml.etree import tostring
from prompt.prompt import *
from chatGPT.api import chatgpt
from langchain_core.output_parsers import PydanticOutputParser
from model.response_model import (
    NewsExtractWithXpath,
    SingleXpath,
    UnwantedXpathExtract,
    Judgement)
from common.utils import fetch_html, get_clean_text_from_html

fields = ['title', 'published_date', 'author', 'sapo', 'content']
mandatory_fields = ['title', 'published_date', 'content']


class XpathGenerator:
    def __init__(self, url, max_retries=2):
        self.url = url
        self.html_content = fetch_html(url)
        self.max_retries = max_retries

    def execute_xpath(self, xpath):
        try:
            tree = html.fromstring(self.html_content)
            node = tree.xpath(xpath)[0]
            return node.text_content()
        except Exception as e:
            print("Extracting failed for xpath: ", xpath)
            return ''

    def judgement(self, extracted_value, expected_value):
        try:
            print("\nJudging " + '-' * 50)
            print(f"Extracted value:\n{extracted_value}")
            print(f"Expected value:\n{expected_value}")
            parser = PydanticOutputParser(pydantic_object=Judgement)
            format_instructions = parser.get_format_instructions()
            prompt = judgement_prompt.format(extracted_value=extracted_value, expected_value=expected_value, format_instructions=format_instructions)
            response = chatgpt(prompt, system_prompt)
            response_dict = parser.invoke(response).dict()
            print(f"Thought: {response_dict['thought']}")
            print(f"Judgement: {response_dict['judgement']}")
            return response_dict['judgement']
        except Exception as e:
            print(f"Judgement failed: {e}")
            return ""

    def single_extract(self, expected_value, html_content):
        try:
            print(f"\nExtracting {expected_value[:150]}...")
            parser = PydanticOutputParser(pydantic_object=SingleXpath)
            format_instructions = parser.get_format_instructions()
            prompt = single_extract_prompt.format(html_content=html_content, expected_value=expected_value, format_instructions=format_instructions)
            response = chatgpt(prompt, system_prompt)
            response_dict = parser.invoke(response).dict()
            xpath = response_dict['xpath']

            return xpath
        except Exception as e:
            print(f"Single extract failed: {e}")
            return ""

    # judgement: consistent/insufficient/excess/unrelated
    def field_extract(self, xpath, expected_value):
        try:
            if expected_value == '':
                print(f"\nTry to extract empty string. Exiting...")
                return ""
            print(f"\nTargeting string: {expected_value}")
            tree = html.fromstring(self.html_content)
            judgement = ''
            for i in range(self.max_retries):
                print(f"\nAttempt {i + 1}")
                if judgement == 'insufficient':
                    # Zoom out
                    xpath += '/..'
                    temp_xpath = xpath
                    node = tree.xpath(xpath)[0]
                    children = node.getchildren()
                    html_content = ''.join([html.tostring(child, encoding='unicode') for child in children])
                    xpath = self.single_extract(expected_value, html_content)

                    print(f"Xpath: {xpath}")
                    extracted_value = self.execute_xpath(xpath)
                    if extracted_value == '':
                        print("Extracted value is empty")
                        judgement = 'unrelated'
                        xpath = temp_xpath
                        continue
                    judgement = self.judgement(extracted_value=extracted_value, expected_value=expected_value)
                    xpath = temp_xpath + xpath

                elif judgement == 'excess':
                    # Zoom in
                    temp_xpath = xpath
                    node = tree.xpath(xpath)[0]
                    children = node.getchildren()
                    html_content = ''.join([html.tostring(child, encoding='unicode') for child in children])
                    xpath = self.single_extract(expected_value, html_content)
                    xpath = temp_xpath + xpath

                    print(f"Xpath: {xpath}")
                    extracted_value = self.execute_xpath(xpath)
                    if extracted_value == '':
                        print("Extracted value is empty")
                        xpath = temp_xpath
                        continue
                    judgement = self.judgement(extracted_value=extracted_value, expected_value=expected_value)

                elif judgement == 'unrelated':
                    # Restart from base html
                    html_content = self.html_content
                    xpath = self.single_extract(expected_value, html_content)

                    print(f"Xpath: {xpath}")
                    extracted_value = self.execute_xpath(xpath)
                    if extracted_value == '':
                        print("Extracted value is empty")
                        continue
                    judgement = self.judgement(extracted_value=extracted_value, expected_value=expected_value)

                else:
                    # First time extract
                    print(f"Xpath: {xpath}")
                    extracted_value = self.execute_xpath(xpath)
                    if extracted_value == '':
                        print("Extracted value is empty")
                        judgement = 'unrelated'
                        continue
                    judgement = self.judgement(extracted_value=extracted_value, expected_value=expected_value)

                if judgement == 'consistent':
                    print(f"Consistent xpath: {xpath}")
                    return xpath

            return ""
        except Exception as e:
            print(f"Field extract failed: {e}")
            return ""

    def first_extract(self):
        try:
            print("\nFirst extract " + '-' * 50)
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

            print("First extract done")
            print(f"Content dict:\n{content_dict}")
            print(f"Xpath dict:\n{xpath_dict}")
            return content_dict, xpath_dict

        except Exception as e:
            print("First extract failed: ", e)
            return None, None

    def generate(self):
        content_dict, xpath_dict = self.first_extract()
        for field in fields:
            print(f"\nExtracting {field} " + '=' * 50)
            xpath_dict[f"{field}_xpath"] = self.field_extract(xpath_dict[f"{field}_xpath"], content_dict[field])

        return content_dict, xpath_dict
