export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
}

export interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  isProcessing: boolean;
}

export interface ChatProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  isProcessing: boolean;
} 