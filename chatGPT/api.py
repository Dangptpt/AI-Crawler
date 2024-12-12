from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def chatgpt(query, system_message="You are a helpful assistant", temperature=0):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system}"),
            ("human", "{query}"),
        ]
    )
    chain = prompt | llm
    response = chain.invoke(
        {
            "system": system_message,
            "query": query,
        }
    )
    return response
