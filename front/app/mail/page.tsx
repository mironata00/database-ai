'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../layout-with-sidebar'
import { 
  Mail, Inbox, Send, RefreshCw, Search, Star, 
  Trash2, Archive, MailOpen, Paperclip, AlertCircle,
  ChevronLeft, ChevronRight, Settings
} from 'lucide-react'

interface EmailMessage {
  id: string
  message_id: string
  subject: string
  from: string
  to: string
  date: string
  is_read: boolean
  is_flagged: boolean
  has_attachments?: boolean
}

interface EmailBody {
  id: string
  subject: string
  from: string
  to: string
  cc: string
  date: string
  body_text: string
  body_html: string
  attachments: Array<{filename: string, content_type: string, size: number}>
}

export default function MailPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [messages, setMessages] = useState<EmailMessage[]>([])
  const [selectedMessage, setSelectedMessage] = useState<EmailBody | null>(null)
  const [loadingMessage, setLoadingMessage] = useState(false)
  const [currentFolder, setCurrentFolder] = useState('INBOX')
  const [folders, setFolders] = useState<string[]>(['INBOX', 'Sent', 'Drafts', 'Trash'])
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [hasEmailConfig, setHasEmailConfig] = useState(false)

  const API_URL = typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.host}` 
    : 'http://localhost'

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    
    if (!token) {
      router.push('/login')
      return
    }
    
    if (userData) {
      const user = JSON.parse(userData)
      setUser(user)
      
      // Проверяем роль
      if (user.role === 'viewer') {
        alert('Почта недоступна для наблюдателей')
        router.push('/')
        return
      }
      
      // Проверяем настройки почты
      checkEmailConfig()
    }
  }

  const checkEmailConfig = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/mail/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setHasEmailConfig(data.has_imap_configured)
        
        if (data.has_imap_configured) {
          fetchFolders()
          fetchMessages()
        }
      } else if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
      }
    } catch (err) {
      console.error('Error checking email config:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchFolders = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/mail/folders`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.folders && data.folders.length > 0) {
          setFolders(data.folders)
        }
      }
    } catch (err) {
      console.error('Error fetching folders:', err)
    }
  }

  const fetchMessages = async (folder: string = currentFolder) => {
    setRefreshing(true)
    setError('')
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_URL}/api/mail/messages?folder=${encodeURIComponent(folder)}&limit=50`, 
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      } else {
        const data = await response.json()
        setError(data.detail || 'Ошибка загрузки писем')
      }
    } catch (err) {
      setError('Ошибка соединения с сервером')
    } finally {
      setRefreshing(false)
    }
  }

  const fetchMessageBody = async (msgId: string) => {
    setLoadingMessage(true)
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_URL}/api/mail/messages/${msgId}?folder=${encodeURIComponent(currentFolder)}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setSelectedMessage(data)
        
        // Помечаем как прочитанное
        if (!messages.find(m => m.id === msgId)?.is_read) {
          markAsRead(msgId)
        }
      }
    } catch (err) {
      console.error('Error fetching message:', err)
    } finally {
      setLoadingMessage(false)
    }
  }

  const markAsRead = async (msgId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      await fetch(`${API_URL}/api/mail/messages/${msgId}/read`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ folder: currentFolder })
      })
      
      // Обновляем локальное состояние
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, is_read: true } : m
      ))
    } catch (err) {
      console.error('Error marking as read:', err)
    }
  }

  const handleFolderChange = (folder: string) => {
    setCurrentFolder(folder)
    setSelectedMessage(null)
    fetchMessages(folder)
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const isToday = date.toDateString() === now.toDateString()
      
      if (isToday) {
        return date.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
      }
      return date.toLocaleDateString('ru', { day: '2-digit', month: 'short' })
    } catch {
      return dateStr
    }
  }

  const extractEmail = (from: string) => {
    const match = from.match(/<(.+?)>/)
    return match ? match[1] : from
  }

  const extractName = (from: string) => {
    const match = from.match(/^"?([^"<]+)"?\s*</)
    return match ? match[1].trim() : extractEmail(from)
  }

  // Фильтрация писем
  const filteredMessages = messages.filter(m => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return m.subject.toLowerCase().includes(q) || 
           m.from.toLowerCase().includes(q)
  })

  if (loading) {
    return (
      <LayoutWithSidebar>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
            <div className="text-gray-500">Загрузка...</div>
          </div>
        </div>
      </LayoutWithSidebar>
    )
  }

  if (!hasEmailConfig) {
    return (
      <LayoutWithSidebar>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="bg-white rounded-lg border p-8 max-w-md text-center">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-yellow-600" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Почта не настроена</h2>
            <p className="text-gray-500 mb-6">
              Для доступа к почте администратор должен настроить IMAP/SMTP параметры для вашей учётной записи.
            </p>
            {user?.role === 'admin' && (
              <button
                onClick={() => router.push('/managers')}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Настроить в разделе Менеджеры
              </button>
            )}
          </div>
        </div>
      </LayoutWithSidebar>
    )
  }

  return (
    <LayoutWithSidebar>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">Почта</h1>
            <span className="text-sm text-gray-500">{user?.email}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchMessages()}
              disabled={refreshing}
              className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
              title="Обновить"
            >
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar - Folders */}
          <div className="w-48 bg-white border-r flex flex-col">
            <div className="p-3">
              <button className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center justify-center space-x-2">
                <Send className="w-4 h-4" />
                <span>Написать</span>
              </button>
            </div>
            
            <nav className="flex-1 px-2 py-2 space-y-1 overflow-y-auto">
              {folders.map(folder => (
                <button
                  key={folder}
                  onClick={() => handleFolderChange(folder)}
                  className={`w-full flex items-center space-x-2 px-3 py-2 rounded-lg text-left text-sm ${
                    currentFolder === folder 
                      ? 'bg-blue-50 text-blue-700' 
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <Inbox className="w-4 h-4" />
                  <span>{folder}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Message List */}
          <div className="w-80 bg-white border-r flex flex-col">
            {/* Search */}
            <div className="p-3 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Поиск..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
              {error && (
                <div className="p-4 text-center text-red-500 text-sm">{error}</div>
              )}
              
              {filteredMessages.length === 0 && !error && (
                <div className="p-8 text-center text-gray-500">
                  <Mail className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Нет писем</p>
                </div>
              )}

              {filteredMessages.map(msg => (
                <button
                  key={msg.id}
                  onClick={() => fetchMessageBody(msg.id)}
                  className={`w-full p-3 border-b text-left hover:bg-gray-50 ${
                    selectedMessage?.id === msg.id ? 'bg-blue-50' : ''
                  } ${!msg.is_read ? 'bg-white' : 'bg-gray-50'}`}
                >
                  <div className="flex items-start space-x-2">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      msg.is_read ? 'bg-transparent' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className={`text-sm truncate ${!msg.is_read ? 'font-semibold' : ''}`}>
                          {extractName(msg.from)}
                        </span>
                        <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
                          {formatDate(msg.date)}
                        </span>
                      </div>
                      <p className={`text-sm truncate ${!msg.is_read ? 'font-medium' : 'text-gray-600'}`}>
                        {msg.subject || '(без темы)'}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Message View */}
          <div className="flex-1 bg-white flex flex-col">
            {loadingMessage ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : selectedMessage ? (
              <>
                {/* Message Header */}
                <div className="p-4 border-b">
                  <h2 className="text-xl font-semibold mb-2">
                    {selectedMessage.subject || '(без темы)'}
                  </h2>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm">
                        <span className="text-gray-500">От:</span>{' '}
                        <span className="font-medium">{selectedMessage.from}</span>
                      </p>
                      <p className="text-sm">
                        <span className="text-gray-500">Кому:</span>{' '}
                        {selectedMessage.to}
                      </p>
                      {selectedMessage.cc && (
                        <p className="text-sm">
                          <span className="text-gray-500">Копия:</span>{' '}
                          {selectedMessage.cc}
                        </p>
                      )}
                    </div>
                    <span className="text-sm text-gray-400">
                      {formatDate(selectedMessage.date)}
                    </span>
                  </div>
                  
                  {/* Attachments */}
                  {selectedMessage.attachments && selectedMessage.attachments.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {selectedMessage.attachments.map((att, idx) => (
                        <div key={idx} className="flex items-center space-x-1 bg-gray-100 px-2 py-1 rounded text-sm">
                          <Paperclip className="w-3 h-3" />
                          <span>{att.filename}</span>
                          <span className="text-gray-400">
                            ({Math.round(att.size / 1024)}KB)
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Message Body */}
                <div className="flex-1 overflow-auto p-4">
                  {selectedMessage.body_html ? (
                    <div 
                      className="prose max-w-none"
                      dangerouslySetInnerHTML={{ __html: selectedMessage.body_html }}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap font-sans text-sm">
                      {selectedMessage.body_text}
                    </pre>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <MailOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Выберите письмо для просмотра</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </LayoutWithSidebar>
  )
}
