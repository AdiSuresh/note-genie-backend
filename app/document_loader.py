from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import torch

class DocumentLoader:
    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            content = f.read()
            chunks = text_splitter.split_text(content)
        return chunks
