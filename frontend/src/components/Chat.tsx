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

    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
          maxWidth: '80%',
          marginLeft: isUser ? 'auto' : '0',
          marginRight: isUser ? '0' : 'auto',
        }}
      >
        <Paper
          sx={{
            p: 2,
            bgcolor: isUser ? 'primary.dark' : 'background.paper',
            borderRadius: 2,
            width: '100%',
          }}
        >
          <Typography 
            variant="body1" 
            sx={{ 
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: 1.6
            }}
          >
            {message.content}
          </Typography>
          
          {/* Display Tables */}
          {message.tables?.map((table, index) => (
            <Box
              key={`table-${index}`}
              sx={{
                mt: 2,
                overflowX: 'auto',
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  '& th, & td': {
                    border: '1px solid',
                    borderColor: 'divider',
                    p: 1,
                    textAlign: 'left',
                  },
                },
              }}
              dangerouslySetInnerHTML={{ __html: table }}
            />
          ))}
          
          {/* Display Images */}
          {message.images?.map((image, index) => (
            <Box
              key={`image-${index}`}
              sx={{
                mt: 2,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              <img
                src={`data:image/png;base64,${image}`}
                alt={`Image ${index + 1}`}
                style={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '4px',
                }}
              />
            </Box>
          ))}
        </Paper>
      </Box>
    );
  };

  return (
    <Box 
      sx={{ 
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          bgcolor: 'background.default',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            bgcolor: 'background.default',
          },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: 'primary.main',
            borderRadius: '4px',
          },
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
          bgcolor: 'background.paper',
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isProcessing}
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'background.paper',
              }
            }}
          />
          <IconButton
            type="submit"
            color="primary"
            disabled={!input.trim() || isProcessing}
            sx={{ 
              p: 1,
              bgcolor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&.Mui-disabled': {
                bgcolor: 'action.disabledBackground',
              }
            }}
          >
            {isProcessing ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default Chat; 