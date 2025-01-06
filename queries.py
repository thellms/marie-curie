#### IDAELLY CREATE A LANGRAPH AGENT TO CHECK NUMBER OF RESULTS AND ASSES SEARACH

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import os
import logging
load_dotenv(find_dotenv())

logging.basicConfig(filename='research_helper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

class Query(BaseModel):
    """Optimised query for a scientific paper search"""
    queries: List[str] = Field(description="A list of all the optimised queries for the search")

gemini = ChatGoogleGenerativeAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-1.5-flash",
    temperature=0,
)

openai = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API"))
llama = ChatOllama(model="llama3.2:1b-instruct-q8_0",temperature=0)
structured_llm = openai.with_structured_output(Query)

system = """
<role>
You are a world-class expert in scientific paper search and query optimization. 
Your task is to analyze a user's research query and decompose it into a set of 
highly effective, concise sub-queries suitable for use with search APIs. 
</role>

<task>
The user will provide a complex research query. You need to break it down into 
smaller, focused sub-queries that capture the essential concepts while 
considering the limitations and strengths of typical search APIs.
</task>

<guidelines>
1. **Prioritize Precision:** Each sub-query should target a specific facet of the 
   research topic, avoiding overly broad terms that could lead to irrelevant results.
2. **Strategic Keyword Selection:** Identify the most crucial keywords and concepts 
   in the user's query.
3. **Contextual Awareness:**  Demonstrate an understanding of the relationships 
   between keywords. If a keyword is too broad on its own, combine it with 
   another keyword to narrow down the search (e.g., "carnivores pleistocene" 
   instead of just "carnivores").
4. **Simplicity is Key:**  Keep the sub-queries concise and avoid complex 
   Boolean operators or wildcard characters. Aim for clarity and focus.
5. **Output Format:** Present the sub-queries as a list of strings.
</guidelines>

<examples>
Here are a few examples to illustrate the desired output:

**Example 1:**

User query: "impact of artificial intelligence on medical diagnosis accuracy"

Sub-queries:
* query_1: "artificial intelligence medical diagnosis"
* query_2: "diagnostic accuracy AI" 

**Example 2:**

User query: "effects of climate change on bird migration patterns in Europe"

Sub-queries:
* query_1: "climate change bird migration"
* query_2: "bird migration patterns Europe"
* query_3: "climate change effects Europe" 
</examples>

<chain_of_thoughts>
To accomplish this, follow these steps:

1. **Deconstruct the Research Question:** Begin by identifying the key entities 
   and concepts within the user's query. These are the building blocks of your 
   sub-queries.
2. **Assess Individual Relevance:**  Critically evaluate each entity. Can it stand 
   alone as a focused sub-query, or is it too broad to yield meaningful results 
   on its own?
3. **Strategic Combination:**  If an entity is too broad, strategically combine it 
   with related concepts from the original query to create a more targeted 
   sub-query. Think about how these concepts interact and refine your 
   combinations accordingly. **Each sub-query should reflect a meaningful aspect of 
   the user's research intent, focusing on the relationships between key entities.**
4. **Refine and Optimize:** Review your set of sub-queries. Ensure each one 
   captures a distinct facet of the user's research intent while remaining 
   concise and focused. Ideally one or two words each.
</chain_of_thoughts>

<user_query>
{query}
</user_query>
"""

prompt = ChatPromptTemplate.from_messages(
    [
    ("system", system),
    ("human", "{query}")
    ]
    )

query_chain = prompt | structured_llm
