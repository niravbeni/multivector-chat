import logging
import os
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import (
    Text, Title, NarrativeText, ListItem, Table, Image, ElementMetadata
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for document content
class DocumentSection:
    def __init__(self, content: str, page_num: int, section_type: str, metadata: Any):
        self.content = content
        self.page_num = page_num
        self.section_type = section_type
        self.metadata = metadata

class DocumentStore:
    def __init__(self):
        self.sections: List[DocumentSection] = []
        self.images: List[Dict[str, Any]] = []
        self.tables: List[Dict[str, Any]] = []
        self.current_document: str = ""  # Add document name tracking

    def clear(self):
        self.sections = []
        self.images = []
        self.tables = []
        self.current_document = ""

    def set_current_document(self, filename: str):
        self.current_document = filename

    def add_section(self, section: DocumentSection):
        self.sections.append(section)
        
    def add_image(self, image_data: str, page_num: int, metadata: Union[Dict[str, Any], ElementMetadata]):
        metadata_dict = metadata.__dict__ if isinstance(metadata, ElementMetadata) else metadata
        self.images.append({
            "data": image_data,
            "page_num": page_num,
            "metadata": metadata_dict
        })
        
    def add_table(self, table_data: str, page_num: int, metadata: Union[Dict[str, Any], ElementMetadata]):
        metadata_dict = metadata.__dict__ if isinstance(metadata, ElementMetadata) else metadata
        self.tables.append({
            "data": table_data,
            "page_num": page_num,
            "metadata": metadata_dict
        })
        
    def get_context_for_query(self, query: str, max_sections: int = 5) -> List[Dict[str, Any]]:
        # TODO: Implement semantic search to find relevant sections
        # For now, return the most recent sections
        relevant_sections = []
        for section in self.sections[-max_sections:]:
            relevant_sections.append({
                "content": section.content,
                "page": section.page_num,
                "type": section.section_type,
                "citation": f"Page {section.page_num}"
            })
        return relevant_sections

# Global document store
document_store = DocumentStore()

def extract_content_from_pdf(file_path: str) -> None:
    try:
        logger.info(f"Extracting content from PDF: {file_path}")
        elements = partition_pdf(
            filename=file_path,
            extract_images_in_pdf=True,
            extract_tables=True,
            strategy="hi_res",  # Use high resolution strategy for better extraction
            infer_table_structure=True,  # Enable table structure inference
            include_metadata=True,
            include_page_breaks=True,
            extract_image_block_types=["Image", "Table"],  # Extract both images and table images
            extract_image_block_to_payload=True  # Extract images as base64
        )
        
        # Get the filename from the path
        filename = os.path.basename(file_path)
        if filename.startswith('temp_'):  # Remove the temp_ prefix if present
            filename = filename[5:]
            
        # Clear previous document store and set the current document
        global document_store
        document_store.clear()
        document_store.set_current_document(filename)
        
        for element in elements:
            # Get page number with fallback to 1 if not available
            page_num = getattr(element.metadata, 'page_number', 1) or 1
            
            if isinstance(element, Table):
                logger.info(f"Found table on page {page_num}")
                
                # Convert table to HTML format
                table_content = ""
                
                # Try to get structured data from the table
                if hasattr(element, 'metadata') and hasattr(element.metadata, 'text_as_html'):
                    # Use HTML if available
                    table_content = str(element.metadata.text_as_html)
                else:
                    # Convert table content to rows
                    table_text = str(element)
                    lines = table_text.strip().split('\n')
                    rows = []
                    current_row = []
                    
                    for line in lines:
                        if line.strip():
                            current_row.append(line.strip())
                            if len(current_row) >= 3:  # Assuming 3 columns
                                rows.append(current_row)
                                current_row = []
                    
                    if current_row:  # Add any remaining cells
                        rows.append(current_row)
                    
                    # Convert rows to HTML
                    table_html = ["<table border='1'>"]
                    if rows:
                        for i, row in enumerate(rows):
                            table_html.append("<tr>")
                            for cell in row:
                                tag = "th" if i == 0 else "td"
                                table_html.append(f"<{tag}>{cell}</{tag}>")
                            table_html.append("</tr>")
                    table_html.append("</table>")
                    table_content = "\n".join(table_html)
                
                if table_content:
                    # Store table content
                    document_store.add_table(
                        table_content,
                        page_num,
                        element.metadata
                    )
                    logger.info(f"Added table content from page {page_num}")
                
                # Check for table image in metadata
                if hasattr(element, 'metadata') and hasattr(element.metadata, 'image_base64'):
                    logger.info(f"Found table image on page {page_num}")
                    document_store.add_image(
                        str(element.metadata.image_base64),
                        page_num,
                        {"type": "table_image", **element.metadata.__dict__}
                    )
                
            elif isinstance(element, Image):
                logger.info(f"Found image on page {page_num}")
                # Try multiple ways to get image data
                image_data = None
                
                # Check all possible image data sources
                if hasattr(element, 'metadata'):
                    if hasattr(element.metadata, 'image_base64'):
                        image_data = element.metadata.image_base64
                        logger.info("Found image_base64 in metadata")
                    elif hasattr(element.metadata, 'image'):
                        image_data = element.metadata.image
                        logger.info("Found image in metadata")
                
                if not image_data and hasattr(element, 'text'):
                    # Sometimes base64 data is stored in text
                    if element.text and element.text.startswith(('data:image', 'iVBOR', '/9j/')):
                        image_data = element.text
                        logger.info("Found base64 image data in text")
                
                # Try to get image from element's dictionary representation
                if not image_data:
                    element_dict = element.to_dict() if hasattr(element, 'to_dict') else {}
                    if 'image_base64' in element_dict:
                        image_data = element_dict['image_base64']
                        logger.info("Found image_base64 in element dictionary")
                
                if image_data:
                    # Clean up base64 data
                    if isinstance(image_data, str):
                        if image_data.startswith('data:image'):
                            # Extract just the base64 part
                            image_data = image_data.split(',')[1]
                        elif not any(image_data.startswith(prefix) for prefix in ('iVBOR', '/9j/')):
                            # If it's not a recognized base64 format, skip it
                            logger.warning(f"Unrecognized image data format on page {page_num}")
                            continue
                    
                    document_store.add_image(
                        str(image_data),
                        page_num,
                        {"type": "standalone_image", **element.metadata.__dict__}
                    )
                    logger.info(f"Added image from page {page_num}")
                else:
                    logger.warning(f"Could not extract data for image on page {page_num}")
            
            elif isinstance(element, (Text, Title)):
                # Only add non-table text to avoid duplication
                if not any(
                    table["page_num"] == page_num and element.text in table["data"]
                    for table in document_store.tables
                ):
                    document_store.add_section(DocumentSection(
                        content=element.text,
                        page_num=page_num,
                        section_type='title' if isinstance(element, Title) else 'text',
                        metadata=element.metadata
                    ))
                    
        logger.info("Content extraction completed successfully")
        logger.info(f"Extracted {len(document_store.sections)} sections, {len(document_store.images)} images, and {len(document_store.tables)} tables")
        
    except Exception as e:
        logger.exception(f"Error extracting content from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting content: {str(e)}")

class Message(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = []
    tables: Optional[List[str]] = []

class ChatRequest(BaseModel):
    messages: List[Message]

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    logger.info(f"Received file upload request: {file.filename}")
    
    if not file or not file.filename:
        logger.error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")
        
    if not file.filename.endswith('.pdf'):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the uploaded file temporarily
    temp_path = os.path.join(os.getcwd(), f"temp_{file.filename}")
    logger.info(f"Saving file to temporary path: {temp_path}")
    
    try:
        # Ensure the file content is at the beginning
        await file.seek(0)
        content = await file.read()
        
        logger.info(f"Read {len(content)} bytes from uploaded file")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Successfully saved file to {temp_path}")
        
        # Verify file exists and is readable
        if not os.path.exists(temp_path):
            logger.error(f"File not found after saving: {temp_path}")
            raise HTTPException(status_code=500, detail="Error saving uploaded file")
            
        if not os.access(temp_path, os.R_OK):
            logger.error(f"File not readable: {temp_path}")
            raise HTTPException(status_code=500, detail="Cannot read uploaded file")
        
        # Process the PDF
        logger.info("Starting PDF processing")
        extract_content_from_pdf(temp_path)
        logger.info("PDF processing completed successfully")
        
        # Only return a summary and preview of text content
        return {
            "message": f"Document processed successfully. Found {len(document_store.sections)} sections of text, "
                      f"{len(document_store.images)} images, and {len(document_store.tables)} tables.",
            "preview": [
                {
                    "content": section.content,
                    "page": section.page_num,
                    "type": section.section_type,
                    "source": file.filename
                }
                for section in document_store.sections[:3]  # First 3 sections as preview
            ]
        }
    except Exception as e:
        logger.exception(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

@app.post("/api/extract")
async def extract_file(file: UploadFile):
    logger.info(f"Received file extraction request: {file.filename}")
    
    if not file or not file.filename:
        logger.error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")
        
    if not file.filename.endswith('.pdf'):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the uploaded file temporarily
    temp_path = os.path.join(os.getcwd(), f"temp_{file.filename}")
    logger.info(f"Saving file to temporary path: {temp_path}")
    
    try:
        # Ensure the file content is at the beginning
        await file.seek(0)
        content = await file.read()
        
        logger.info(f"Read {len(content)} bytes from uploaded file")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Successfully saved file to {temp_path}")
        
        # Process the PDF
        extract_content_from_pdf(temp_path)  # The function will handle setting the document name
        
        # Only return a summary of what was extracted
        return {
            "message": f"Document processed successfully. Found {len(document_store.sections)} sections of text, "
                      f"{len(document_store.images)} images, and {len(document_store.tables)} tables.",
            "preview": [
                {
                    "content": section.content,
                    "page": section.page_num,
                    "type": section.section_type,
                    "source": document_store.current_document  # Use the stored document name
                }
                for section in document_store.sections[:3]  # First 3 sections as preview
            ]
        }
    except Exception as e:
        logger.exception(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages")
        
        # Get the user's question from the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
                
        if not user_message:
            logger.error("No user message found in the request")
            raise HTTPException(status_code=400, detail="No user message found in the request")
        
        logger.info(f"Processing user message: {user_message}")
        
        # Get relevant context for the question
        context = document_store.get_context_for_query(user_message)
        
        if not context:
            logger.warning("No relevant context found for the query")
            return Message(
                role="assistant",
                content="I don't have enough context to answer your question. Please try asking something else or upload a document first.",
                images=[],
                tables=[]
            )
        
        # Format the response with citations including document name
        response_parts = []
        citations = []
        relevant_pages = set()
        
        for section in context:
            if section["content"].strip():
                citation = f"[Source: {document_store.current_document}, Page {section['page']}]"
                response_parts.append(f"{section['content']} {citation}")
                citations.append(citation)
                relevant_pages.add(section["page"])
        
        # Check if the query is asking about images or tables
        query_lower = user_message.lower()
        include_images = any(term in query_lower for term in ['image', 'picture', 'figure', 'diagram', 'graph', 'show me', 'visual'])
        include_tables = any(term in query_lower for term in ['table', 'data', 'values', 'rows', 'columns', 'entries'])
        
        # Include images and tables only if requested or if they're on the same page as relevant text
        relevant_images = []
        relevant_tables = []
        
        if include_images:
            relevant_images = [
                img["data"]
                for img in document_store.images 
                if img["page_num"] in relevant_pages
            ]
            logger.info(f"Including {len(relevant_images)} relevant images from {document_store.current_document}")
        
        if include_tables:
            relevant_tables = [
                table["data"]
                for table in document_store.tables 
                if table["page_num"] in relevant_pages
            ]
            logger.info(f"Including {len(relevant_tables)} relevant tables from {document_store.current_document}")
        
        logger.info(f"Returning response with context from {len(relevant_pages)} pages of {document_store.current_document}")
        
        return Message(
            role="assistant",
            content="\n\n".join(response_parts),
            images=relevant_images,
            tables=relevant_tables
        )
        
    except Exception as e:
        logger.exception(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)