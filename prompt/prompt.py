

system_prompt = "You are a web parser specializing in news and understanding HTML code, and you can provide clear executable code in the browser."


extract_prompt = """Here is a news webpage HTML.
1. Extract the content from the news webpage.
2. From the extracted content, identify the XPath selector in the HTML that leads to the content extracted in the previous step. Here are some rule for XPath selector to be output:
- Do not output the xpath with "contains" or "text()=" function.
- It is discouraged to output the xpath that uses numerical indexes to select specific occurrences of elements within a set.
- It would be appreciate to use more @class or @style to identify different node that may share the same xpath expression.
- If the HTML code doesn't contain the suitable information match the instruction, output empty string.
- Avoid using some string function such as 'substring()' and 'normalize-space()' to normalize the text in the node.
- The XPath selector should be strictly executable.

{format_instructions}

Here is the HTML: 
{html_content}"""


extract_unwanted_prompt = """Here is the main content of a news article and a piece of the HTML that contains that content.
Return a list of XPaths of the elements, which are:
1. The elements that cause noise, not part of the main content of the article, such as ads, related posts, etc,. which, if removed, would not affect the integrity of the article's content.
2. Not figure or image elements.
If no such tags exist, return an empty list
The output xpath should be relative which start with '//'.

{format_instructions}

Main content of news: 
{content}

HTML of news content: 
{content_html}"""


judgement_prompt = """Your main task is to judge the consistency of the extracted value compared to the expected value, which is recognized beforehand. Here are some hints for your judgement:
    1) Validate only on semantic aspect. Do not take redundant separators, extra spaces, or line breaks into consideration, as we can post-process them.
    2) Consistency is considered "excess" if the extracted result contains elements that are not part of the expected value.
    3) Consistency is considered "insufficient" if the extracted result does not contain enough elements from the expected value.
    4) Consistency is considered "consistent" if the extracted result contains all the expected elements, including semantic correctness.
    5) Consistency is considered "unrelated" if the extracted result and the expected value are completely unrelated to each other.

{format_instructions}

The extracted value is: {extracted_value}
The expected value is: {expected_value}"""


single_extract_prompt = """Provide the expected value to search for and the HTML. Extract the XPath leading to the element in the HTML that contains the expected value.
Here are some rule for XPath selector to be output:
- Do not output the xpath with "contains" or "text()=" function.
- It is discouraged to output the xpath that uses numerical indexes to select specific occurrences of elements within a set.
- It would be appreciate to use more @class or @style to identify different node that may share the same xpath expression.
- If the HTML code doesn't contain the suitable information match the instruction, output empty string.
- Avoid using some string function such as 'substring()' and 'normalize-space()' to normalize the text in the node.
- The XPath selector should be strictly executable.

{format_instructions}

Expected value:
{expected_value}

HTML:
{html_content}"""
