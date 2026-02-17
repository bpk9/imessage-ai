'use client'

import { useState, useEffect } from 'react'

interface Conversation {
  id: string
  display_name: string
  participants: string[]
  message_count: number
  last_message_date: string
  is_group: boolean
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchConversations()
  }, [])

  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/conversations')
      if (!response.ok) {
        throw new Error('Failed to fetch conversations')
      }
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (err) {
      setError('Failed to load conversations. Make sure the FastAPI server is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMs = now.getTime() - date.getTime()
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInDays === 0) return 'Today'
    if (diffInDays === 1) return 'Yesterday'
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`
    return `${Math.floor(diffInDays / 365)} years ago`
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Conversations</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchConversations}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Conversations</h1>
        <p className="text-gray-600">Browse your message history</p>
      </div>

      {conversations.length === 0 ? (
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Conversations Found</h2>
          <p className="text-gray-600 mb-4">
            Make sure your messages have been indexed. Run the indexer first.
          </p>
          <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Index Messages
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {conversations.map((conversation) => (
            <div 
              key={conversation.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-gray-900">
                      {conversation.display_name || conversation.participants.join(', ')}
                    </h3>
                    {conversation.is_group && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        Group
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {conversation.participants.length} participant{conversation.participants.length !== 1 ? 's' : ''}
                  </p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>{conversation.message_count.toLocaleString()} messages</span>
                    <span>•</span>
                    <span>Last active {formatDate(conversation.last_message_date)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <button className="text-blue-500 hover:text-blue-600 text-sm font-medium">
                    View →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      {conversations.length > 0 && (
        <div className="mt-8 bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {conversations.length}
              </div>
              <div className="text-sm text-gray-600">Total Conversations</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {conversations.reduce((sum, conv) => sum + conv.message_count, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Messages</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {conversations.filter(conv => conv.is_group).length}
              </div>
              <div className="text-sm text-gray-600">Group Chats</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(conversations.reduce((sum, conv) => sum + conv.message_count, 0) / conversations.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Messages</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}