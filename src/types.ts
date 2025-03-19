export interface ChatMessage {
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  images?: string[] // Base64 encoded images
  context?: {
    text: string[]
    images: string[]
  }
}

export interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>
}

export interface ChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => Promise<void>
} 