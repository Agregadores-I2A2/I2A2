# funcoes/arquivos.py

import os
import zipfile
import pandas as pd
import sqlite3
import tempfile
from langchain.agents import Tool
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI


PERSIST_DIRECTORY = 'chroma.db'
SQLITE_DB_PATH = 'trabalho.db'

def get_embedding():
    """Fetches embeddings using HuggingFace."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def process_csv(file):
    """Processes CSV files and returns split document chunks."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        temp_file.write(file.getvalue())
        temp_file_path = temp_file.name

    loader = CSVLoader(temp_file_path, encoding='utf-8')
    docs = loader.load()
    os.remove(temp_file_path)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    return text_splitter.split_documents(docs)

def import_base(zip_path: str, extract_to: str) -> bool:
    """Extracts CSV files from a zip archive and saves data to an SQLite database."""
    try:
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Arquivo ZIP não encontrado: {zip_path}")
        
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        arqu_antigo_cab = f'{extract_to}202401_NFs_Cabecalho.csv'
        arqu_antigo_item = f'{extract_to}202401_NFs_Itens.csv'
        arq_nv_cab = f'{extract_to}Cabecalho.csv'
        arq_nv_item = f'{extract_to}Itens.csv'
        
        if os.path.exists(arq_nv_cab):
            os.remove(arq_nv_cab)
        if os.path.exists(arq_nv_item):
            os.remove(arq_nv_item)
        
        os.rename(arqu_antigo_cab, arq_nv_cab)
        os.rename(arqu_antigo_item, arq_nv_item)
        
        conexao = sqlite3.connect(SQLITE_DB_PATH)
        extract_to_path = Path(extract_to)
        for arquivo in extract_to_path.glob('*.csv'):
            df = pd.read_csv(arquivo)
            df.columns = [col.replace(' ', '_') for col in df.columns]
            df.to_sql(arquivo.stem, conexao, if_exists='replace', index=False)
        
        conexao.close()
        return True
    except Exception as e:
        print(f"Erro na importação: {e}")
        return False

def load_existing_vector_store():
    """Carrega o armazenamento vetorial existente, se disponível."""
    if os.path.exists(PERSIST_DIRECTORY):
        return Chroma.load_from_directory(PERSIST_DIRECTORY)
    return None


def load_embedding():
    """Loads or initializes embeddings."""
    
    if not os.path.exists(PERSIST_DIRECTORY):
        return None
    
    return Chroma(
        embedding_function=get_embedding(),
        persist_directory=PERSIST_DIRECTORY,
    )

vector_store = load_embedding() or Chroma(embedding_function=get_embedding(), persist_directory=PERSIST_DIRECTORY)


def add_to_vector_store(chunks, vector_store=None):
    """Updates or creates a new vector store."""
    if vector_store:
        vector_store.add_documents(chunks)
    else:
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=get_embedding(),
            persist_directory=PERSIST_DIRECTORY,
        )
    return vector_store

def load_llm(model_name: str) -> ChatOpenAI:
    """Carrega o modelo LLM da Groq."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY não encontrado no .env")
    return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.2)

def create_rag_tool(llm_model, vector_store):
    """Creates the RAG (Retrieval-Augmented Generation) tool for querying a vectorized document store."""
    def rag_tool_func(query):
        if not vector_store:
            return "⚠️ Nenhum documento foi carregado ainda. Faça upload de arquivos CSV com legislação primeiro."
        # Placeholder for a function that executes the query on the documents
        response = "Response from RAG query"
        return response
    
    return Tool.from_function(
        func=rag_tool_func,
        name="Consulta_Legislacao_RAG",
        description="Use para responder perguntas sobre leis e regras fiscais baseadas nos documentos carregados."
    )

def create_sql_prefix():
    """Cria e retorna um template de prefixo SQL para padronizar queries."""
    template = """
    SELECT coluna1, coluna2 FROM tabela
    WHERE condicao1 = valor1 AND condicao2 = valor2
    ORDER BY coluna1 DESC;
    """
    return template