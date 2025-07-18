'use client'

import React from 'react'
import { CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid'
import { clsx } from 'clsx'
import { ProcessingStep } from '../types/api'

interface ProgressStepperProps {
  steps: ProcessingStep[]
  currentStep: number
}

export function ProgressStepper({ steps, currentStep }: ProgressStepperProps) {
  const getStepIcon = (step: ProcessingStep, index: number) => {
    if (step.status === 'completed') {
      return <CheckIcon className="w-5 h-5 text-white" />
    }
    if (step.status === 'error') {
      return <ExclamationTriangleIcon className="w-5 h-5 text-white" />
    }
    if (step.status === 'processing') {
      return (
        <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
      )
    }
    return <span className="text-sm font-medium text-gray-500">{index + 1}</span>
  }

  const getStepColor = (step: ProcessingStep, index: number) => {
    if (step.status === 'completed') return 'bg-green-500'
    if (step.status === 'error') return 'bg-red-500'
    if (step.status === 'processing') return 'bg-blue-500'
    if (index <= currentStep) return 'bg-gray-300'
    return 'bg-gray-200'
  }

  const getConnectorColor = (index: number) => {
    if (index < steps.length - 1) {
      const nextStep = steps[index + 1]
      if (nextStep.status === 'completed') return 'bg-green-500'
      if (steps[index].status === 'completed') return 'bg-gray-300'
    }
    return 'bg-gray-200'
  }

  return (
    <div className="w-full">
      <nav aria-label="Progress">
        <ol className="flex items-center justify-between">
          {steps.map((step, index) => (
            <li key={step.id} className="relative flex-1">
              <div className="flex items-center">
                {/* Step circle */}
                <div
                  className={clsx(
                    'relative flex items-center justify-center w-10 h-10 rounded-full',
                    getStepColor(step, index)
                  )}
                >
                  {getStepIcon(step, index)}
                </div>
                
                {/* Connector line */}
                {index < steps.length - 1 && (
                  <div
                    className={clsx(
                      'absolute top-5 left-10 w-full h-0.5 -translate-y-1/2',
                      getConnectorColor(index)
                    )}
                  />
                )}
              </div>
              
              {/* Step details */}
              <div className="mt-3">
                <p className={clsx(
                  'text-sm font-medium',
                  {
                    'text-green-600': step.status === 'completed',
                    'text-red-600': step.status === 'error',
                    'text-blue-600': step.status === 'processing',
                    'text-gray-900': step.status === 'pending' && index <= currentStep,
                    'text-gray-500': step.status === 'pending' && index > currentStep,
                  }
                )}>
                  {step.name}
                </p>
                
                {step.timing && step.status === 'completed' && (
                  <p className="text-xs text-gray-500 mt-1">
                    {step.timing.toFixed(2)}s
                  </p>
                )}
                
                {step.error && step.status === 'error' && (
                  <p className="text-xs text-red-600 mt-1">
                    {step.error}
                  </p>
                )}
                
                {step.status === 'processing' && (
                  <p className="text-xs text-blue-600 mt-1">
                    Processing...
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </nav>
    </div>
  )
} 