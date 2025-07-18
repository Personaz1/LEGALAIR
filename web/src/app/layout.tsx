import React from 'react'
import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Legal ASI - Document Analysis Platform',
  description: 'AI-powered legal document processing with OCR, classification, and advisory services',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm border-b">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                  <div className="flex items-center">
                    <h1 className="text-xl font-semibold text-gray-900">
                      Legal ASI
                    </h1>
                    <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      v1.0.0-preGPU
                    </span>
                  </div>
                  <nav className="flex space-x-4">
                    <a href="/" className="text-gray-600 hover:text-gray-900">
                      Upload
                    </a>
                    <a href="/docs" className="text-gray-600 hover:text-gray-900">
                      API Docs
                    </a>
                  </nav>
                </div>
              </div>
            </header>
            <main>{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
} 