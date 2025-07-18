'use client'

import React, { useState } from 'react'
import { UploadDropzone } from '../components/UploadDropzone'
import { ProgressStepper } from '../components/ProgressStepper'
import { JsonViewer } from '../components/JsonViewer'
import { useDocumentProcessing } from '../hooks/useDocumentProcessing'
import { ArrowPathIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

export default function HomePage() {
  const [results, setResults] = useState<any>(null)
  const [showRawData, setShowRawData] = useState(false)

  const { state, processDocument, reset, isProcessing } = useDocumentProcessing({
    onComplete: (allResults) => {
      setResults(allResults)
    },
    onError: (error) => {
      console.error('Processing error:', error)
    }
  })

  const handleFileSelect = (file: File) => {
    if (!isProcessing) {
      setResults(null)
      setShowRawData(false)
      processDocument(file)
    }
  }

  const handleReset = () => {
    reset()
    setResults(null)
    setShowRawData(false)
  }

  const getAdviceRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'high': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Document Analysis Platform
        </h1>
        <p className="text-lg text-gray-600">
          Upload a legal document to extract text, classify type, identify entities, and get AI-powered analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Section */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Upload Document
            </h2>
            
            <UploadDropzone
              onFileSelect={handleFileSelect}
              isProcessing={isProcessing}
              acceptedTypes={['image/*', 'application/pdf']}
              maxSize={10 * 1024 * 1024}
            />

            {state.file && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <DocumentTextIcon className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      {state.file.name}
                    </p>
                    <p className="text-xs text-blue-700">
                      {(state.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              </div>
            )}

            {(state.file || results) && (
              <button
                onClick={handleReset}
                disabled={isProcessing}
                className="mt-4 w-full btn-secondary flex items-center justify-center space-x-2"
              >
                <ArrowPathIcon className="w-4 h-4" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Processing Section */}
        <div className="lg:col-span-2">
          {state.file && (
            <div className="card mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Processing Pipeline
              </h2>
              <ProgressStepper steps={state.steps} currentStep={state.currentStep} />
            </div>
          )}

          {state.error && (
            <div className="card mb-6 border-red-200 bg-red-50">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <h3 className="text-lg font-medium text-red-800">Processing Error</h3>
              </div>
              <p className="text-red-700">{state.error}</p>
            </div>
          )}

          {/* Results Section */}
          {results && (
            <div className="space-y-6">
              {/* Legal Advice Card */}
              {results.advice && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    AI Legal Analysis
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-gray-700">Risk Level:</span>
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getAdviceRiskColor(results.advice.analysis.risk_level)}`}>
                          {results.advice.analysis.risk_level.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">
                          ({(results.advice.analysis.confidence * 100).toFixed(1)}% confidence)
                        </span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
                      <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                        {results.advice.analysis.document_summary}
                      </p>
                    </div>

                    {results.advice.analysis.key_issues?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Key Issues</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {results.advice.analysis.key_issues.map((issue: string, index: number) => (
                            <li key={index} className="flex items-start space-x-2">
                              <span className="text-red-500 mt-1">•</span>
                              <span>{issue}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {results.advice.analysis.recommendations?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {results.advice.analysis.recommendations.map((rec: string, index: number) => (
                            <li key={index} className="flex items-start space-x-2">
                              <span className="text-green-500 mt-1">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Document Classification */}
              {results.classification && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Document Classification
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-gray-700">Type:</span>
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                          {results.classification.document_type}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-700">Confidence:</span>
                        <span className="text-sm text-gray-600">
                          {(results.classification.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    {results.classification.fields && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">Extracted Fields:</p>
                        <div className="text-xs text-gray-600 space-y-1">
                          {results.classification.fields.amounts?.length > 0 && (
                            <p>Amounts: {results.classification.fields.amounts.length}</p>
                          )}
                          {results.classification.fields.dates?.length > 0 && (
                            <p>Dates: {results.classification.fields.dates.length}</p>
                          )}
                          {results.classification.fields.persons?.length > 0 && (
                            <p>Persons: {results.classification.fields.persons.length}</p>
                          )}
                          {results.classification.fields.organizations?.length > 0 && (
                            <p>Organizations: {results.classification.fields.organizations.length}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Raw Data Toggle */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Raw Data</h3>
                  <button
                    onClick={() => setShowRawData(!showRawData)}
                    className="btn-secondary text-sm"
                  >
                    {showRawData ? 'Hide' : 'Show'} JSON
                  </button>
                </div>
                
                {showRawData && (
                  <JsonViewer 
                    data={results} 
                    title="Complete Processing Results"
                    maxHeight="500px"
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 