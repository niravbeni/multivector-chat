import { useState, useRef, useEffect } from 'react'
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import { ChatProps, ChatMessage } from '../types'

const Chat = ({ messages, onSendMessage }: ChatProps) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      await onSendMessage(input.trim())
      setInput('')
    }
  }

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user'

    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start',
            maxWidth: '70%',
          }}
        >
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : 'secondary.main',
              m: 1,
            }}
          >
            {isUser ? 'U' : 'A'}
          </Avatar>
          <Paper
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.dark' : 'background.paper',
              borderRadius: 2,
            }}
          >
            <Typography variant="body1">{message.content}</Typography>
            {message.images?.map((image, index) => (
              <img
                key={index}
                src={`data:image/jpeg;base64,${image}`}
                alt={`Response image ${index + 1}`}
                style={{
                  maxWidth: '100%',
                  height: 'auto',
                  marginTop: '8px',
                  borderRadius: '4px',
                }}
              />
            ))}
          </Paper>
        </Box>
      </Box>
    )
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          bgcolor: 'background.default',
        }}
      >
        {messages.map((message, index) => (
          <div key={index}>{renderMessage(message)}</div>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            variant="outlined"
            size="small"
          />
          <IconButton
            type="submit"
            color="primary"
            disabled={!input.trim()}
            sx={{ p: '10px' }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>
    </Box>
  )
}

export default Chat 