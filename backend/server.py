import logging
import os
from typing import Dict, List, Any
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from unstructured.partition.pdf import partition_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_content_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text and other content from PDF using unstructured library."""
    logger.info(f"Starting PDF extraction from {file_path}")
    
    try:
        # Partition the PDF into elements
        logger.info("Calling partition_pdf...")
        chunks = partition_pdf(
            filename=file_path,
            infer_table_structure=True,            # extract tables
            strategy="hi_res",                     # mandatory to infer tables
            extract_image_block_types=["Image", "Table"],   # Extract both images and tables as images
            extract_image_block_to_payload=True,   # if true, will extract base64 for API usage
            chunking_strategy="by_title",          # or 'basic'
            max_characters=10000,                  # defaults to 500
            combine_text_under_n_chars=2000,       # defaults to 0
            new_after_n_chars=6000
        )
        logger.info(f"Found {len(chunks)} chunks in the PDF")
        
        # Debug chunk types
        chunk_types = set([str(type(el)) for el in chunks])
        logger.info(f"Chunk types found: {chunk_types}")
        
        # Extract text and images (including tables as images)
        text_content: List[str] = []
        images: List[str] = []
        
        def debug_element(element: Any, prefix: str = "") -> None:
            """Debug an element's attributes and metadata."""
            logger.info(f"{prefix}Element type: {type(element).__name__}")
            logger.info(f"{prefix}Element attributes: {dir(element)}")
            if hasattr(element, 'metadata'):
                logger.info(f"{prefix}Has metadata")
                logger.info(f"{prefix}Metadata attributes: {dir(element.metadata)}")
                if hasattr(element.metadata, 'to_dict'):
                    try:
                        metadata_dict = element.metadata.to_dict()
                        logger.info(f"{prefix}Metadata dict: {metadata_dict}")
                    except Exception as e:
                        logger.error(f"{prefix}Error getting metadata dict: {str(e)}")
            if hasattr(element, 'to_dict'):
                try:
                    element_dict = element.to_dict()
                    logger.info(f"{prefix}Element dict: {element_dict}")
                except Exception as e:
                    logger.error(f"{prefix}Error getting element dict: {str(e)}")
        
        # Process chunks
        for chunk in chunks:
            chunk_type = str(type(chunk))
            logger.info(f"\nProcessing chunk of type: {chunk_type}")
            debug_element(chunk, "CHUNK: ")
            
            # Handle CompositeElements
            if "CompositeElement" in chunk_type:
                # Add text
                text_content.append(str(chunk))
                logger.info("Added text from composite chunk")
                
                # Process composite element
                if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
                    orig_elements = chunk.metadata.orig_elements
                    if orig_elements:
                        logger.info(f"Found {len(orig_elements)} original elements")
                        
                        # Debug element types
                        element_types = [str(type(el)) for el in orig_elements]
                        logger.info(f"Original element types: {element_types}")
                        
                        # Extract both images and tables as images
                        visual_elements = [el for el in orig_elements if any(t in str(type(el)) for t in ["Image", "Table"])]
                        logger.info(f"Found {len(visual_elements)} visual elements (images/tables) in composite")
                        
                        for element in visual_elements:
                            try:
                                # Try to get base64 from metadata
                                if hasattr(element, 'metadata') and hasattr(element.metadata, 'image_base64'):
                                    base64_data = element.metadata.image_base64
                                    if base64_data:
                                        images.append(f"data:image/png;base64,{base64_data}")
                                        logger.info(f"Added {type(element).__name__} from metadata base64")
                                        continue
                                
                                # Try to get from element dict
                                if hasattr(element, 'to_dict'):
                                    element_dict = element.to_dict()
                                    if 'image_base64' in element_dict:
                                        base64_data = element_dict['image_base64']
                                        if base64_data:
                                            images.append(f"data:image/png;base64,{base64_data}")
                                            logger.info(f"Added {type(element).__name__} from element dict")
                            except Exception as e:
                                logger.error(f"Error processing visual element: {str(e)}")
        
        logger.info(f"\nExtraction Summary:")
        logger.info(f"Extracted {len(text_content)} text elements")
        logger.info(f"Extracted {len(images)} visual elements (images/tables)")
        
        return {
            "text": "\n".join(text_content),
            "images": images
        }
    except Exception as e:
        logger.error(f"Error extracting content from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """Extract content from uploaded PDF file."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Create a temporary file to store the upload
        temp_path = f"temp_{file.filename}"
        try:
            # Save uploaded file
            with open(temp_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            
            # Process the PDF
            result = extract_content_from_pdf(temp_path)
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)