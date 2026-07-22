"""
LLM Client — Google Gemini via LangChain
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def get_llm(temperature: float = 0.1, model: str = "gemini-2.0-flash") -> ChatGoogleGenerativeAI:
    """Get Gemini LLM instance"""
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GEMINI_API_KEY,
        temperature=temperature,
        max_tokens=8192,
    )


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Get Gemini embedding model"""
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def invoke_llm(prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
    """Invoke Gemini with retry logic"""
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(temperature=temperature)
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    return response.content


async def ainvoke_llm(prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
    """Async invoke Gemini"""
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(temperature=temperature)
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    response = await llm.ainvoke(messages)
    return response.content
