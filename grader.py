import logging
import pandas as pd
import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from cache_utils import get_cached_result, store_result_in_cache, log_llm_call
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logging.basicConfig(filename='research_helper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

# # LLM setup for grading
# gemini = ChatGoogleGenerativeAI(
#     api_key=os.getenv("GEMINI_API_KEY"),
#     model="gemini-1.5-flash",
#     temperature=0,
# )

llama = ChatOllama(model="llama3.2:1b-instruct-q8_0", temperature=0)
groq = ChatGroq(model="llama-3.3-70b-versatile",temperature=0, api_key=os.getenv("GROQ_API_KEY"))
openai = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API"))

class Grade(BaseModel):
    """Grade for relevance of a scientific paper abstract"""
    is_relevant: bool = Field(description="Is the abstract relevant to the user query?")

structured_llm = openai.with_structured_output(Grade)

system_prompt = """
<role>
You are an expert research assistant tasked with evaluating the relevance of 
scientific papers. You will be provided with a user's research query and the 
abstract of a scientific paper.
</role>

<task>
Carefully analyze the abstract and determine if the paper is likely to be 
relevant to the user's research query. 
</task>

<guidelines>
- Consider the key concepts and entities in the user query.
- Assess whether the abstract discusses those concepts and entities in a 
  meaningful way.
- If the abstract provides information or insights that could help answer the 
  user's research question, then the paper is relevant.
- Respond with "yes" if the paper is relevant, "no" if it is not.
</guidelines>

<user_query>
{query}
</user_query>

<abstract>
{abstract}
</abstract>
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{abstract}")
    ]
)

grader_chain = prompt | structured_llm

def grade_paper(user_query: str, abstract: str, doi: str = None) -> bool:
    """
    Grades the relevance of a paper based on its abstract and the user query,
    using caching to avoid redundant LLM calls.
    
    Args:
        user_query (str): The original user query or search topic.
        abstract (str): The paper's abstract.
        doi (str, optional): The paper's DOI (or a fallback).
    
    Returns:
        bool: True if the paper is deemed relevant, False otherwise.
    """
    try:
        # 1) Check if a cached result already exists
        cached_result = get_cached_result(doi)
        if cached_result is not None:
            logging.info(f"Using cached result for DOI={doi}")
            return cached_result

        # 2) Invoke the LLM chain
        grade_obj = grader_chain.invoke({"query": user_query, "abstract": abstract})
        is_relevant = grade_obj.is_relevant

        # 3) Store the result in the cache
        store_result_in_cache(doi, is_relevant)

        # 4) Log the LLM call
        log_llm_call(
            user_query=user_query,
            abstract=abstract,
            response=is_relevant,
            model_name="gpt-4o-mini",  # or whichever model you prefer
            doi=doi,
        )

        return is_relevant
    except Exception as e:
        logging.error(f"Error grading paper: {e}")
        return False
