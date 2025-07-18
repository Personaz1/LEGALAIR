'use client'

import React, { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

interface JsonViewerProps {
  data: any
  title?: string
  className?: string
  maxHeight?: string
}

export function JsonViewer({ data, title, className, maxHeight = '400px' }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={clsx('bg-gray-900 rounded-lg overflow-hidden', className)}>
      {title && (
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
          <h3 className="text-sm font-medium text-gray-200">{title}</h3>
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
          >
            {copied ? (
              <>
                <CheckIcon className="w-4 h-4" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <ClipboardIcon className="w-4 h-4" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      )}
      
      <div
        className="p-4 overflow-auto text-sm font-mono"
        style={{ maxHeight }}
      >
        <JsonNode data={data} level={0} />
      </div>
    </div>
  )
}

interface JsonNodeProps {
  data: any
  level: number
  isLast?: boolean
  parentKey?: string
}

function JsonNode({ data, level, isLast = true, parentKey }: JsonNodeProps) {
  const [collapsed, setCollapsed] = useState(level > 1)
  
  const indent = '  '.repeat(level)
  
  if (data === null) {
    return <span className="text-gray-500">null</span>
  }
  
  if (typeof data === 'string') {
    return <span className="text-green-400">"{data}"</span>
  }
  
  if (typeof data === 'number') {
    return <span className="text-blue-400">{data}</span>
  }
  
  if (typeof data === 'boolean') {
    return <span className="text-purple-400">{data.toString()}</span>
  }
  
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span className="text-gray-400">[]</span>
    }
    
    return (
      <div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center text-gray-400 hover:text-gray-200 transition-colors"
        >
          {collapsed ? (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          )}
          <span>[{data.length}]</span>
        </button>
        
        {!collapsed && (
          <div className="ml-4 border-l border-gray-700 pl-4">
            {data.map((item, index) => (
              <div key={index} className="py-1">
                <span className="text-gray-500">{index}: </span>
                <JsonNode
                  data={item}
                  level={level + 1}
                  isLast={index === data.length - 1}
                />
                {index < data.length - 1 && <span className="text-gray-500">,</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
  
  if (typeof data === 'object') {
    const entries = Object.entries(data)
    
    if (entries.length === 0) {
      return <span className="text-gray-400">{'{}'}</span>
    }
    
    return (
      <div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center text-gray-400 hover:text-gray-200 transition-colors"
        >
          {collapsed ? (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          )}
          <span>{'{'}{entries.length}{'}'}</span>
        </button>
        
        {!collapsed && (
          <div className="ml-4 border-l border-gray-700 pl-4">
            {entries.map(([key, value], index) => (
              <div key={key} className="py-1">
                <span className="text-yellow-400">"{key}"</span>
                <span className="text-gray-500">: </span>
                <JsonNode
                  data={value}
                  level={level + 1}
                  isLast={index === entries.length - 1}
                  parentKey={key}
                />
                {index < entries.length - 1 && <span className="text-gray-500">,</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
  
  return <span className="text-gray-500">{String(data)}</span>
} 