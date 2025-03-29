from langchain_ollama import ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ContextChat:
    vector_store = None
    retriever = None
    chain = None

    def __init__(self):
        self.model = ChatOllama(model="deepseek-r1:1.5b")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        self.prompt = PromptTemplate.from_template("""
        <s> [INST] You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. [/INST] </s> 
[INST] Question: {question} 
Context: {context} 
Answer: [/INST]""")

    def ingest(self, path:str):
        docs = PyPDFLoader(file_path=path).load()
        chunks = self.text_splitter.split_documents(docs)
        chunks = filter_complex_metadata(chunks)
        vector_store = Chroma.from_documents(documents=chunks, embedding=FastEmbedEmbeddings())
        self.retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.5
            }
        )

        self.chain = ({"context": self.retriever,
                       "question": RunnablePassthrough()}
                    | self.prompt
                    | self.model
                    |StrOutputParser()
                      )

    def ask(self, query:str):
        if not self.chain:
            return "Add docs"

        return self.chain.invoke(query)

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None



if __name__ == "__main__":
    chat = ContextChat()
    chat.ingest("147125512.pdf")
    while True:
        q = input("Question >")
        print(chat.ask(q))