import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Box, Paper, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import { FileUploadProps } from '../types'

const FileUpload = ({ onFileUpload }: FileUploadProps) => {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        if (file.type === 'application/pdf') {
          await onFileUpload(file)
        } else {
          alert('Please upload a PDF file')
        }
      }
    },
    [onFileUpload]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  })

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '80vh'
      }}
    >
      <Paper
        {...getRootProps()}
        sx={{
          p: 6,
          textAlign: 'center',
          cursor: 'pointer',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          borderRadius: 2,
          '&:hover': {
            bgcolor: 'action.hover'
          }
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, mb: 2, color: 'primary.main' }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the PDF here' : 'Drag & drop a PDF file here'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          or click to select a file
        </Typography>
      </Paper>
    </Box>
  )
}

export default FileUpload 