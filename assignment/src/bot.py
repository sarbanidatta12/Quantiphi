import os
from pathlib import Path
from langchain_openai import AzureChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain 
from langchain.prompts import (
    SystemMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.schema import BaseRetriever
from utils import read_config
from prompt import generate_system_message

os.environ["OPENAI_API_VERSION"] = "2024-02-01"

def get_prompt(system_message):
    """
    Generates a chat prompt template for an AI support agent to answer customer queries.
    
    Args:
        system_message (str): The system message template.
    
    Returns:
        ChatPromptTemplate: The chat prompt template.
    """
    prompt = ChatPromptTemplate(
        input_variables=['context', 'input'],  # Include 'context' here
        messages=[
            SystemMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['context', 'input'],  # Update to include 'context'
                    template=system_message,
                    template_format='f-string',
                    validate_template=True
                ),
                additional_kwargs={}
            ),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['input'],
                    template='{input}\nHelpful Answer:',
                    template_format='f-string',
                    validate_template=True
                ),
                additional_kwargs={}
            )
        ]
    )
    return prompt

def make_chain(organization_names):
    """
    Creates a retrieval chain for answering queries based on the specified organization names.
    
    Args:
        organization_names (list): List of organization names.
    
    Returns:
        RetrievalChain: The retrieval chain for answering queries.
    """
    # Initialize the AzureChatOpenAI model
    model = AzureChatOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY1"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT1"),
        azure_deployment="gpt-4o-mini",
        openai_api_version=os.getenv("OPENAI_API_VERSION"),
        temperature=0.1
    )

    # Read configuration file
    config_file_path = Path(__file__).parent / 'config.yaml'
    config = read_config(config_file_path)
    
    # Set base data path and vectorstore paths
    base_data_path = Path(config['folder_path']) / 'vectorstore'
    vectorstore_paths = [base_data_path / org for org in organization_names]

    # Set device for embeddings (CPU or GPU)
    device = config.get("device", "cpu")
    
    # Initialize embeddings model
    embeddings = HuggingFaceEmbeddings(model_name=config.get("embed_model"), model_kwargs={'device': device})

    # Initialize vector stores
    vector_stores = [Chroma(persist_directory=str(path), embedding_function=embeddings) for path in vectorstore_paths]
    
    # Generate system message and prompt
    system_message = generate_system_message(organization_names)
    prompt = get_prompt(system_message)   

    class CombinedRetriever(BaseRetriever):
        def __init__(self, retrievers):
            super().__init__()  # Ensure proper initialization of the parent class
            self._retrievers = retrievers  # Use a private field to avoid conflicts
        
        def get_relevant_documents(self, query):
            results = []
            for retriever in self._retrievers:  # Use the private field here
                results.extend(retriever.get_relevant_documents(query))
            return results

        async def aget_relevant_documents(self, query):  # For async compatibility
            results = []
            for retriever in self._retrievers:
                results.extend(await retriever.aget_relevant_documents(query))
            return results
        
        def with_config(self, config=None, **kwargs):
            return self
    
    
    retrievers = [vector_store.as_retriever(search_type="similarity", verbose=True, k=10) for vector_store in vector_stores]
    
    # Initialize combined retriever
    combined_retriever = CombinedRetriever(retrievers)
    
    # Create document combination chain
    combine_docs_chain = create_stuff_documents_chain(llm=model, prompt=prompt)    
    
    # Create retrieval chain using the combined retriever
    chain = create_retrieval_chain(
        retriever=combined_retriever,
        combine_docs_chain=combine_docs_chain
    )
    return chain

def get_response(question, organization_names):
    """
    Generates a response based on the input question by using a history-aware retrieval chain.
    
    Args:
        question (str): The input question.
        organization_names (list): List of organization names.
    
    Returns:
        str: The response to the input question.
    """
    chat_history = [] 
    chain = make_chain(organization_names)      
    
    input_text = f"Organization Names: {organization_names}\n" \
                    f"Chat History: {chat_history}\n" \
                    f"Question: {question}"
                         
    response = chain.invoke({"input": input_text})   
    return response['answer']

# Example usage
if __name__ == "__main__":
    # Organization information
    organization_names = ["Home Bancorp", "Selective Insurance"]

    # Get response
    response = get_response("How many daily active users are there across Meta's Family of Apps?", organization_names)
    print("Answer:", response)