export interface OCRResponse {
  success: boolean
  text: string
  confidence: number
  processing_time: number
  metadata: {
    total_chars: number
    lines_detected: number
    language: string
  }
}

export interface ClassificationResponse {
  success: boolean
  document_type: string
  confidence: number
  processing_time: number
  sections?: {
    header: {
      text: string
      boundaries: [number, number]
      completeness: number
    }
    body: {
      text: string
      boundaries: [number, number]
      completeness: number
    }
    footer: {
      text: string
      boundaries: [number, number]
      completeness: number
    }
  }
  fields?: {
    amounts: Array<{
      value: number
      currency: string
      confidence: number
      position: [number, number]
    }>
    dates: Array<{
      value: string
      format: string
      confidence: number
      position: [number, number]
    }>
    persons: Array<{
      name: string
      role: string
      confidence: number
      position: [number, number]
    }>
    organizations: Array<{
      name: string
      type: string
      confidence: number
      position: [number, number]
    }>
    legal_articles: Array<{
      article: string
      description: string
      confidence: number
      position: [number, number]
    }>
  }
}

export interface NERResponse {
  success: boolean
  entities: Array<{
    text: string
    label: string
    confidence: number
    start: number
    end: number
  }>
  processing_time: number
}

export interface AdviceResponse {
  success: boolean
  analysis: {
    document_summary: string
    key_issues: string[]
    recommendations: string[]
    risk_level: 'low' | 'medium' | 'high'
    confidence: number
  }
  processing_time: number
}

export interface ProcessingStep {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  result?: any
  error?: string
  timing?: number
}

export interface DocumentProcessingState {
  file: File | null
  steps: ProcessingStep[]
  currentStep: number
  isProcessing: boolean
  error?: string
} 