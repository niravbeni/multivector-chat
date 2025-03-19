import { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { ChatProps, ChatMessage } from '../types';

const Chat = ({ messages, onSendMessage, isProcessing }: ChatProps) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';

    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
        }}
      >
        <Paper
          sx={{
            p: 2,
            maxWidth: '70%',
            backgroundColor: isSystem
              ? 'warning.dark'
              : isUser
              ? 'primary.dark'
              : 'background.paper',
          }}
        >
          <Typography>{message.content}</Typography>
          {message.images?.map((image, index) => (
            <Box
              key={index}
              component="img"
              src={image}
              alt={`Image ${index + 1}`}
              sx={{
                mt: 1,
                maxWidth: '100%',
                height: 'auto',
                borderRadius: 1,
              }}
            />
          ))}
        </Paper>
      </Box>
    );
  };

  return (
    <Paper
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '70vh',
      }}
    >
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
        }}
      >
        {messages.map((message, index) => (
          <div key={index}>{renderMessage(message)}</div>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          gap: 1,
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isProcessing}
        />
        <IconButton
          type="submit"
          color="primary"
          disabled={!input.trim() || isProcessing}
        >
          {isProcessing ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Box>
    </Paper>
  );
};

export default Chat; 