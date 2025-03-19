import { useState } from 'react'
import {
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material'
import axios, { AxiosError } from 'axios'
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
      const response = await axios.post(`${BACKEND_URL}/api/extract`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      const { message } = response.data

      setMessages([
        {
          role: 'system',
          content: 'Document loaded successfully. I can now answer questions about its text, tables, and images.',
        },
        {
          role: 'assistant',
          content: message,
        },
      ])

      setIsFileUploaded(true)
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{ detail: string }>
      console.error('Error uploading file:', axiosError)
      setMessages([
        {
          role: 'system',
          content: `Error processing document: ${axiosError.response?.data?.detail || axiosError.message}`,
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

    // Add user message to UI immediately
    setMessages([...messages, { role: 'user', content: message }])
    setIsProcessing(true)

    try {
      // Format messages for the backend, excluding system messages
      const chatMessages = messages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({
          role: msg.role,
          content: msg.content,
          ...(msg.images && { images: msg.images }),
          ...(msg.tables && { tables: msg.tables })
        }))

      // Add the new user message
      chatMessages.push({ role: 'user', content: message })

      const response = await axios.post(`${BACKEND_URL}/api/chat`, { 
        messages: chatMessages
      })

      // Add assistant's response to UI
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: response.data.role,
          content: response.data.content,
          images: response.data.images || [],
          tables: response.data.tables || []
        },
      ])
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{ detail: string }>
      console.error('Error sending message:', axiosError)
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          role: 'system',
          content: `Error processing message: ${axiosError.response?.data?.detail || axiosError.message}`,
        },
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box 
        sx={{ 
          width: '100vw',
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
          overflow: 'hidden'
        }}
      >
        <Box 
          sx={{
            width: '90%',
            maxWidth: '800px',
            height: '90%',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            p: 2,
          }}
        >
          <Box sx={{ flexShrink: 0 }}>
            <FileUpload onFileUpload={handleFileUpload} isProcessing={isProcessing} />
          </Box>
          <Box sx={{ 
            flex: 1,
            minHeight: 0, // Important for proper flex behavior
            position: 'relative',
            bgcolor: 'background.paper',
            borderRadius: 2,
            boxShadow: 3
          }}>
            <Chat
              messages={messages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
            />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
