import { useState } from 'react'
import { Box, Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import FileUpload from './components/FileUpload'
import Chat from './components/Chat'
import { ChatMessage } from './types'
import axios from 'axios'

const API_URL = 'http://localhost:3001'

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
})

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isFileUploaded, setIsFileUploaded] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleFileUpload = async (file: File) => {
    console.log('Processing file:', file.name)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      // Upload file to backend
      await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      // Add initial system message
      setMessages([{
        content: `I've loaded the document "${file.name}". I can now answer questions about its text, tables, and images. How can I help you analyze it?`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      }])
      
      setIsFileUploaded(true)
    } catch (error) {
      console.error('Error uploading file:', error)
      alert('Error uploading file. Please try again.')
    }
  }

  const handleSendMessage = async (message: string) => {
    if (isProcessing) return // Prevent multiple submissions while processing

    const newMessage: ChatMessage = {
      content: message,
      role: 'user',
      timestamp: new Date().toISOString(),
    }
    
    setMessages(prev => [...prev, newMessage])
    setIsProcessing(true)

    try {
      // Send message to backend
      const response = await axios.post(`${API_URL}/chat`, { message })
      
      const botResponse: ChatMessage = {
        content: response.data.response,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        images: response.data.context.images // Add images from context if available
      }
      
      setMessages(prev => [...prev, botResponse])
    } catch (error) {
      console.error('Error processing message:', error)
      const errorMessage: ChatMessage = {
        content: "I'm sorry, but I encountered an error processing your request. Please try again.",
        role: 'assistant',
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box 
        sx={{ 
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          p: 2
        }}
      >
        <Container 
          maxWidth="md" 
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            height: '100vh'
          }}
        >
          <Box sx={{ width: '100%', maxWidth: '800px' }}>
            {!isFileUploaded ? (
              <FileUpload onFileUpload={handleFileUpload} />
            ) : (
              <Chat messages={messages} onSendMessage={handleSendMessage} />
            )}
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  )
}

export default App
