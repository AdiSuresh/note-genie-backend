from fastapi import FastAPI
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from app.models.query_request import QueryRequest

app = FastAPI()

template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""

model = OllamaLLM(model='deepseek-r1:1.5b')

prompt = ChatPromptTemplate.from_template(template=template)

chain = prompt | model

@app.get("/")
def get_root():
    return {"message": "Hello, FastAPI!"}

@app.post('/query')
def post_query(request: QueryRequest):
    result = chain.invoke({
        'context': request.context,
        'question': request.question
    })
    
    return {'result': result}
