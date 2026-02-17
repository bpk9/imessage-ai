'use client'

import { useState } from 'react'

interface SearchResult {
  content: string
  sender: string
  date: string
  conversation: string
  similarity_score: number
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const search = async () => {
    if (!query.trim()) return

    setIsLoading(true)
    setHasSearched(true)

    try {
      const response = await fetch(`http://localhost:8000/search?query=${encodeURIComponent(query)}&limit=20`)
      if (!response.ok) {
        throw new Error('Search failed')
      }
      const data = await response.json()
      setResults(data.results || [])
    } catch (error) {
      console.error('Search error:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      search()
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const highlightQuery = (text: string, query: string) => {
    if (!query.trim()) return text
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    return text.replace(regex, '<mark className="bg-yellow-200">$1</mark>')
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Search Messages</h1>
        <p className="text-gray-600">Find messages using keywords or semantic search</p>
      </div>

      {/* Search Input */}
      <div className="mb-8">
        <div className="flex space-x-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search your messages..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={search}
            disabled={!query.trim() || isLoading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        <p className="mt-2 text-sm text-gray-500">
          Try: "dinner plans", "what time", "thanks for helping", or any topic you remember discussing
        </p>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse bg-white border border-gray-200 rounded-lg p-4">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : hasSearched ? (
        results.length > 0 ? (
          <div className="space-y-4">
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
              </p>
            </div>
            {results.map((result, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="mb-3">
                  <p 
                    className="text-gray-900"
                    dangerouslySetInnerHTML={{ __html: highlightQuery(result.content, query) }}
                  />
                </div>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center space-x-3">
                    <span className="font-medium">{result.sender}</span>
                    <span>•</span>
                    <span>{formatDate(result.date)}</span>
                    <span>•</span>
                    <span className="italic">{result.conversation}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full" title={`${Math.round(result.similarity_score * 100)}% match`}></div>
                    <span className="text-xs">{Math.round(result.similarity_score * 100)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Results Found</h2>
            <p className="text-gray-600 mb-4">
              Try different keywords or make sure your messages have been indexed.
            </p>
            <div className="text-sm text-gray-500">
              <p>Search tips:</p>
              <ul className="mt-2 space-y-1">
                <li>• Use specific keywords from your conversations</li>
                <li>• Try names, topics, or memorable phrases</li>
                <li>• Search works with synonyms and related concepts</li>
              </ul>
            </div>
          </div>
        )
      ) : (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Search Your Messages</h2>
          <p className="text-gray-600 mb-6">
            Use semantic search to find messages by meaning, not just exact keywords.
          </p>
          <div className="grid md:grid-cols-3 gap-4 text-left">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">🔍 Keywords</h3>
              <p className="text-sm text-gray-600">Search for specific words or phrases that appeared in your messages.</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">🧠 Semantic</h3>
              <p className="text-sm text-gray-600">Find messages by meaning - works even if you don't remember exact words.</p>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">⚡ Fast</h3>
              <p className="text-sm text-gray-600">Instant search across your entire message history with relevance scoring.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}