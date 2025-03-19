import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import { FileUploadProps } from '../types';

const FileUpload = ({ onFileUpload, isProcessing }: FileUploadProps) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileUpload(acceptedFiles[0]);
      }
    },
    [onFileUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: isProcessing,
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 3,
        textAlign: 'center',
        cursor: isProcessing ? 'not-allowed' : 'pointer',
        backgroundColor: (theme) =>
          isDragActive
            ? theme.palette.action.hover
            : theme.palette.background.paper,
      }}
    >
      <input {...getInputProps()} />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
        }}
      >
        {isProcessing ? (
          <>
            <CircularProgress />
            <Typography>Processing document...</Typography>
          </>
        ) : (
          <Typography>
            {isDragActive
              ? 'Drop the PDF here'
              : 'Drag and drop a PDF here, or click to select one'}
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default FileUpload; 