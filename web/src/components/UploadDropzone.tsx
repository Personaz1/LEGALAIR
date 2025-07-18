'use client'

import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { DocumentTextIcon, PhotoIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void
  isProcessing?: boolean
  acceptedTypes?: string[]
  maxSize?: number
}

export function UploadDropzone({ 
  onFileSelect, 
  isProcessing = false,
  acceptedTypes = ['image/*', 'application/pdf'],
  maxSize = 10 * 1024 * 1024 // 10MB
}: UploadDropzoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0])
    }
  }, [onFileSelect])

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    fileRejections
  } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxSize,
    maxFiles: 1,
    disabled: isProcessing
  })

  const getIcon = () => {
    if (acceptedTypes.includes('image/*')) {
      return <PhotoIcon className="w-12 h-12 text-gray-400" />
    }
    return <DocumentTextIcon className="w-12 h-12 text-gray-400" />
  }

  const getUploadText = () => {
    if (isProcessing) return 'Processing...'
    if (isDragReject) return 'File type not supported'
    if (isDragActive) return 'Drop the file here'
    return 'Drag and drop a document, or click to select'
  }

  const getSupportedFormats = () => {
    const formats: string[] = []
    if (acceptedTypes.includes('image/*')) formats.push('Images')
    if (acceptedTypes.includes('application/pdf')) formats.push('PDF')
    return formats.join(', ')
  }

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200',
          {
            'border-blue-300 bg-blue-50': isDragActive && !isDragReject,
            'border-red-300 bg-red-50': isDragReject,
            'border-gray-300 hover:border-gray-400': !isDragActive && !isDragReject && !isProcessing,
            'border-gray-200 bg-gray-50 cursor-not-allowed': isProcessing,
          }
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isDragReject ? (
            <ExclamationTriangleIcon className="w-12 h-12 text-red-400" />
          ) : (
            getIcon()
          )}
          
          <div>
            <p className={clsx(
              'text-lg font-medium',
              {
                'text-blue-600': isDragActive && !isDragReject,
                'text-red-600': isDragReject,
                'text-gray-600': !isDragActive && !isDragReject,
              }
            )}>
              {getUploadText()}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supported formats: {getSupportedFormats()} (max {Math.round(maxSize / 1024 / 1024)}MB)
            </p>
          </div>
        </div>
      </div>

      {fileRejections.length > 0 && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h4 className="text-sm font-medium text-red-800 mb-2">File Upload Errors:</h4>
          <ul className="text-sm text-red-700 space-y-1">
            {fileRejections.map(({ file, errors }) => (
              <li key={file.name}>
                <strong>{file.name}:</strong>
                <ul className="ml-4 list-disc">
                  {errors.map(({ code, message }) => (
                    <li key={code}>{message}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
} 