import os
import uuid
from typing import List, Dict, Any
from langchain.vectorstores import Chroma
from langchain.storage import InMemoryStore
from langchain.schema.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import base64

class RAGHandler:
    def __init__(self):
        # Initialize vector store with OpenAI embeddings
        self.vectorstore = Chroma(
            collection_name="multi_modal_rag",
            embedding_function=OpenAIEmbeddings()
        )
        
        # Initialize document store
        self.docstore = InMemoryStore()
        self.id_key = "doc_id"
        
        # Initialize retriever
        self.retriever = MultiVectorRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            id_key=self.id_key,
        )
        
        # Initialize summarization model
        self.summarize_prompt = ChatPromptTemplate.from_template("""
            You are an assistant tasked with summarizing content from documents.
            Give a concise summary of the content.
            
            Content to summarize: {content}
            
            Respond only with the summary, no additional comments.
            Just give the summary as it is.
        """)
        
        self.image_prompt = ChatPromptTemplate.from_messages([
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": "Describe this image in detail, focusing on its key elements and any text or data it contains."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,{image}"}
                }
            ])
        ])
        
        # Initialize OpenAI model for summaries
        self.model = ChatOpenAI(model="gpt-4-vision-preview")
        
        # Create summary chains
        self.summarize_chain = (
            self.summarize_prompt 
            | self.model 
            | StrOutputParser()
        )
        
        self.image_chain = (
            self.image_prompt 
            | self.model 
            | StrOutputParser()
        )
    
    def process_document(self, texts: List[Dict], tables: List[Dict], images: List[Dict]):
        """Process and store document elements with their summaries"""
        
        # Process texts
        text_ids = [str(uuid.uuid4()) for _ in texts]
        text_summaries = []
        
        for text in texts:
            summary = self.summarize_chain.invoke({"content": text["content"]})
            text_summaries.append(Document(
                page_content=summary,
                metadata={
                    self.id_key: text_ids[len(text_summaries)],
                    "page": text["page_num"],
                    "type": "text"
                }
            ))
        
        # Add texts to stores
        self.vectorstore.add_documents(text_summaries)
        self.docstore.mset(list(zip(text_ids, texts)))
        
        # Process tables
        table_ids = [str(uuid.uuid4()) for _ in tables]
        table_summaries = []
        
        for table in tables:
            summary = self.summarize_chain.invoke({"content": table["data"]})
            table_summaries.append(Document(
                page_content=summary,
                metadata={
                    self.id_key: table_ids[len(table_summaries)],
                    "page": table["page_num"],
                    "type": "table"
                }
            ))
        
        # Add tables to stores
        self.vectorstore.add_documents(table_summaries)
        self.docstore.mset(list(zip(table_ids, tables)))
        
        # Process images
        image_ids = [str(uuid.uuid4()) for _ in images]
        image_summaries = []
        
        for image in images:
            try:
                summary = self.image_chain.invoke({"image": image["data"]})
                image_summaries.append(Document(
                    page_content=summary,
                    metadata={
                        self.id_key: image_ids[len(image_summaries)],
                        "page": image["page_num"],
                        "type": "image"
                    }
                ))
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                continue
        
        # Add images to stores
        self.vectorstore.add_documents(image_summaries)
        self.docstore.mset(list(zip(image_ids, images)))
    
    def get_relevant_content(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant content based on the query"""
        
        # Get relevant documents
        docs = self.retriever.get_relevant_documents(query)
        
        # Separate content by type
        texts = []
        images = []
        tables = []
        
        for doc in docs:
            doc_id = doc.metadata[self.id_key]
            original_content = self.docstore.get(doc_id)
            
            if original_content["type"] == "text":
                texts.append({
                    "content": original_content["content"],
                    "page": original_content["page_num"]
                })
            elif original_content["type"] == "image":
                images.append({
                    "data": original_content["data"],
                    "page": original_content["page_num"]
                })
            elif original_content["type"] == "table":
                tables.append({
                    "data": original_content["data"],
                    "page": original_content["page_num"]
                })
        
        return {
            "texts": texts,
            "images": images,
            "tables": tables
        }
    
    def clear(self):
        """Clear all stored data"""
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            collection_name="multi_modal_rag",
            embedding_function=OpenAIEmbeddings()
        )
        self.docstore = InMemoryStore() 