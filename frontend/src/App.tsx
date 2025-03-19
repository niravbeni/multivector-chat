import { useState } from 'react'
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material'
import axios from 'axios'
import { ChatMessage } from './types'
import FileUpload from './components/FileUpload'
import Chat from './components/Chat'

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
})

// Backend URL with fallback
const BACKEND_URL = 'http://localhost:3001'

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isFileUploaded, setIsFileUploaded] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${BACKEND_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      const { summary, content } = response.data

      setMessages([
        {
          role: 'system',
          content: 'Document loaded successfully. I can now answer questions about its text, tables, and images.',
        },
        {
          role: 'assistant',
          content: `Here's a summary of the document: ${summary}`,
          images: content.images || [],
        },
      ])

      setIsFileUploaded(true)
    } catch (error: any) {
      console.error('Error uploading file:', error)
      setMessages([
        {
          role: 'system',
          content: `Error processing document: ${error.response?.data?.detail || error.message}`,
        },
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSendMessage = async (message: string) => {
    if (!isFileUploaded) {
      setMessages([
        ...messages,
        {
          role: 'system',
          content: 'Please upload a document first.',
        },
      ])
      return
    }

    setMessages([...messages, { role: 'user', content: message }])
    setIsProcessing(true)

    try {
      const response = await axios.post(`${BACKEND_URL}/api/chat`, { 
        messages: [
          ...messages.filter(msg => msg.role !== 'system'),
          { role: 'user', content: message }
        ]
      })
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: 'assistant',
          content: response.data.response,
        },
      ])
    } catch (error: any) {
      console.error('Error sending message:', error)
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: 'system',
          content: `Error processing message: ${error.response?.data?.detail || error.message}`,
        },
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="md">
        <Box
          sx={{
            minHeight: '100vh',
            py: 4,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          <FileUpload onFileUpload={handleFileUpload} isProcessing={isProcessing} />
          <Chat
            messages={messages}
            onSendMessage={handleSendMessage}
            isProcessing={isProcessing}
          />
        </Box>
      </Container>
    </ThemeProvider>
  )
}

export default App
