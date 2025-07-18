'use client'

import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ProcessingStep, DocumentProcessingState, OCRResponse, ClassificationResponse, NERResponse, AdviceResponse } from '../types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UseDocumentProcessingOptions {
  onComplete?: (results: any) => void
  onError?: (error: string) => void
}

export function useDocumentProcessing(options: UseDocumentProcessingOptions = {}) {
  const [state, setState] = useState<DocumentProcessingState>({
    file: null,
    steps: [
      { id: 'ocr', name: 'Text Extraction (OCR)', status: 'pending' },
      { id: 'classify', name: 'Document Classification', status: 'pending' },
      { id: 'ner', name: 'Entity Recognition', status: 'pending' },
      { id: 'advice', name: 'Legal Analysis', status: 'pending' },
    ],
    currentStep: 0,
    isProcessing: false,
  })

  const updateStep = useCallback((stepId: string, updates: Partial<ProcessingStep>) => {
    setState(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
    }))
  }, [])

  const processOCR = useMutation({
    mutationFn: async (file: File): Promise<OCRResponse> => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/ocr/extract`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`OCR failed: ${response.statusText}`)
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      updateStep('ocr', { 
        status: 'completed', 
        result: data, 
        timing: data.processing_time 
      })
    },
    onError: (error) => {
      updateStep('ocr', { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'OCR processing failed' 
      })
    },
  })

  const processClassification = useMutation({
    mutationFn: async (text: string): Promise<ClassificationResponse> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/classify/document?sections=true&fields=true`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      
      if (!response.ok) {
        throw new Error(`Classification failed: ${response.statusText}`)
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      updateStep('classify', { 
        status: 'completed', 
        result: data, 
        timing: data.processing_time 
      })
    },
    onError: (error) => {
      updateStep('classify', { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Classification failed' 
      })
    },
  })

  const processNER = useMutation({
    mutationFn: async (text: string): Promise<NERResponse> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/ner/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      
      if (!response.ok) {
        throw new Error(`NER failed: ${response.statusText}`)
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      updateStep('ner', { 
        status: 'completed', 
        result: data, 
        timing: data.processing_time 
      })
    },
    onError: (error) => {
      updateStep('ner', { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'NER processing failed' 
      })
    },
  })

  const processAdvice = useMutation({
    mutationFn: async (payload: { text: string, document_type: string, entities: any }): Promise<AdviceResponse> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/advise/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      
      if (!response.ok) {
        throw new Error(`Advisory analysis failed: ${response.statusText}`)
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      updateStep('advice', { 
        status: 'completed', 
        result: data, 
        timing: data.processing_time 
      })
    },
    onError: (error) => {
      updateStep('advice', { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Advisory analysis failed' 
      })
    },
  })

  const processDocument = useCallback(async (file: File) => {
    if (state.isProcessing) return

    setState(prev => ({
      ...prev,
      file,
      isProcessing: true,
      currentStep: 0,
      steps: prev.steps.map(step => ({ ...step, status: 'pending', result: undefined, error: undefined, timing: undefined }))
    }))

    try {
      // Step 1: OCR
      updateStep('ocr', { status: 'processing' })
      setState(prev => ({ ...prev, currentStep: 0 }))
      const ocrResult = await processOCR.mutateAsync(file)
      
      if (!ocrResult.success) {
        throw new Error('OCR processing failed')
      }

      // Step 2: Classification  
      updateStep('classify', { status: 'processing' })
      setState(prev => ({ ...prev, currentStep: 1 }))
      const classifyResult = await processClassification.mutateAsync(ocrResult.text)
      
      if (!classifyResult.success) {
        throw new Error('Classification failed')
      }

      // Step 3: NER
      updateStep('ner', { status: 'processing' })
      setState(prev => ({ ...prev, currentStep: 2 }))
      const nerResult = await processNER.mutateAsync(ocrResult.text)
      
      if (!nerResult.success) {
        throw new Error('NER processing failed')
      }

      // Step 4: Advice
      updateStep('advice', { status: 'processing' })
      setState(prev => ({ ...prev, currentStep: 3 }))
      const adviceResult = await processAdvice.mutateAsync({
        text: ocrResult.text,
        document_type: classifyResult.document_type,
        entities: nerResult.entities
      })

      if (!adviceResult.success) {
        throw new Error('Advisory analysis failed')
      }

      // All completed
      setState(prev => ({ ...prev, isProcessing: false, currentStep: 4 }))
      
      const allResults = {
        ocr: ocrResult,
        classification: classifyResult,
        ner: nerResult,
        advice: adviceResult,
      }
      
      options.onComplete?.(allResults)

    } catch (error) {
      setState(prev => ({ ...prev, isProcessing: false }))
      const errorMessage = error instanceof Error ? error.message : 'Processing failed'
      setState(prev => ({ ...prev, error: errorMessage }))
      options.onError?.(errorMessage)
    }
  }, [state.isProcessing, processOCR, processClassification, processNER, processAdvice, updateStep, options])

  const reset = useCallback(() => {
    setState({
      file: null,
      steps: [
        { id: 'ocr', name: 'Text Extraction (OCR)', status: 'pending' },
        { id: 'classify', name: 'Document Classification', status: 'pending' },
        { id: 'ner', name: 'Entity Recognition', status: 'pending' },
        { id: 'advice', name: 'Legal Analysis', status: 'pending' },
      ],
      currentStep: 0,
      isProcessing: false,
    })
  }, [])

  return {
    state,
    processDocument,
    reset,
    isProcessing: state.isProcessing || processOCR.isPending || processClassification.isPending || processNER.isPending || processAdvice.isPending,
  }
} 