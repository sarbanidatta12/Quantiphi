import os
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter 
from langchain.document_loaders import DirectoryLoader, PyPDFLoader

from utils import read_config, find_folders


def build_vectorstore():
    """
    Builds a vector store from documents in specified folders.
    
    Reads the configuration file to get the folder paths and other settings,
    loads documents from the specified folders, splits the documents into chunks,
    and creates a vector store using embeddings.
    """
    config_file_path = Path(__file__).parent / 'config.yaml'
    config = read_config(config_file_path)
    folders = find_folders(config)
    
    base_data_path = Path(config['folder_path'])
    vectorstore_path = base_data_path / 'vectorstore'
    vectorstore_path.mkdir(parents=True, exist_ok=True)
    
    device = config.get("device", "cpu") 
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': device})
    
    for folder in folders:
        folder_path = base_data_path / "documents" / folder
        loader = DirectoryLoader(folder_path, glob="*.pdf", loader_cls=PyPDFLoader, show_progress=False)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        # Build vector store
        Chroma.from_documents(texts, embeddings, persist_directory=str(vectorstore_path / f"{folder}"))
        
if __name__ == "__main__":
    build_vectorstore()