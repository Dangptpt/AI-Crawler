from pydantic import BaseModel, Field


class NewsExtractWithXpath(BaseModel):
    title: str = Field(description="The title of the news article")
    published_date: str = Field(description="The publication date of the article, may include time depends on article.")
    author: str = Field(description="The author of the article. It may or may not be present depending on the "
                                    "article; return a blank if absent.")
    sapo: str = Field(description="The sapo of the article. It may or may not be present depending on the article; return a blank if absent.")
    content: str = Field(description="The content of the article")
    thumb_image_url: str = Field(description="""The URL of the article's thumbnail image. Choose by the following priority:
                                               1. The image located right after the article title.
                                               2. The first image in the article's content.""")
    title_xpath: str = Field(description="The XPath of the article title")
    published_date_xpath: str = Field(description="The XPath of the article's published date")
    author_xpath: str = Field(
        description="The XPath of the article's author. If the author is an empty string, return an empty string.")
    sapo_xpath: str = Field(
        description="The XPath of the article's sapo. If the sapo is an empty string, return an empty string.")
    content_xpath: str = Field(description="The XPath of the article's content")
    # thumb_image_url_xpath: str = Field(description="""The XPath of the article's thumbnail image URL.
    #                                                     If not found, select another thumbnail image according to the priority:
    #                                                     1. The image located right after the article title.
    #                                                     2. The first image in the article's content.
    #                                                     And return an alternative XPath.""")


class SingleXpath(BaseModel):
    xpath: str = Field(description="The extracted XPath.")


class UnwantedXpathExtract(BaseModel):
    unwanted_xpath: list = Field(description="""A list of XPaths of elements that bring the content which cause noise, not part of the main content of the article.
                                            If no such tags exist, return an empty list.""")


class SeedXpath(BaseModel):
    news_url_xpath: str = Field(
        description="The XPath to the href containing the URLs of news articles located in the news listing page. "
                    "Do not include pagination hrefs. ")


class Judgement(BaseModel):
    thought: str = Field(description="A brief thinking about whether the extracted value is consistent with the "
                                     "expected value")
    judgement: str = Field(description="Return consistent/insufficient/excess/unrelated directly")
