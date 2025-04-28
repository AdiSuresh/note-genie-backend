from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentLoader:
    buffer: str = ''
    
    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=0, keep_separator='end')
            self.buffer = content = f.read()
            chunks = text_splitter.split_text(content)
        return chunks
