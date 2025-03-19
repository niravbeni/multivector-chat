# Multivector PDF Processor

A modern web application that processes PDF files to extract text, images, and tables using the unstructured library. The application provides a clean interface to view and interact with the extracted content.

## Features

- Extract text content from PDFs
- Extract and display images from PDFs
- Extract and display tables as images
- Modern web interface for easy interaction
- Real-time processing and display

## Tech Stack

### Backend
- Python with FastAPI
- unstructured library for PDF processing
- Support for OCR and table detection

### Frontend
- Next.js
- React
- Tailwind CSS

## Setup

### System Dependencies

For macOS:
```bash
brew install poppler tesseract libmagic
```

For Linux:
```bash
sudo apt-get install poppler-utils tesseract-ocr libmagic-dev
```

### Python Dependencies

```bash
pip install "unstructured[all-docs]" pillow lxml fastapi uvicorn python-multipart
```

### Running the Application

1. Start the backend server:
```bash
cd backend
PYTHONPATH=. python server.py
```

2. Start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```

3. Open http://localhost:3000 in your browser

## Usage

1. Upload a PDF file using the web interface
2. The application will process the PDF and extract:
   - Text content
   - Images
   - Tables (rendered as images)
3. View the extracted content in the web interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.