'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from './layout-with-sidebar'
import { Search, Loader2, Mail, X, FileText, Upload } from 'lucide-react'

interface Supplier {
  id: string
  name: string
  inn: string
  email: string | null
  rating: number | null
  is_blacklisted: boolean
  tags_array: string[]
  status: string
  color: string
  categories: string[]
}

interface SearchSuggestion {
  type: 'product' | 'category' | 'tag'
  name: string
  sku?: string
  supplier_id?: string
  supplier_name?: string
  count?: number
  score?: number
}

// Простой стемминг для русского языка (убираем окончания)
const stem = (word: string): string => {
  const lower = word.toLowerCase()
  const endings = ['ая', 'яя', 'ой', 'ый', 'ий', 'ые', 'ие', 'ого', 'его', 'ому', 'ему', 'ым', 'им', 'ых', 'их', 'ую', 'юю', 'ою', 'ею', 'ав', 'ев', 'ов', 'ев', 'ая', 'яя']
  
  for (const ending of endings) {
    if (lower.endsWith(ending) && lower.length > ending.length + 2) {
      return lower.slice(0, -ending.length)
    }
  }
  
  if (lower.length > 4) {
    return lower.slice(0, -1)
  }
  
  return lower
}

// Расстояние Левенштейна
const levenshtein = (a: string, b: string): number => {
  const matrix: number[][] = []
  
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i]
  }
  
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j
  }
  
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  
  return matrix[b.length][a.length]
}

// Fuzzy match
const fuzzyMatch = (text: string, query: string): boolean => {
  const textLower = text.toLowerCase()
  const queryLower = query.toLowerCase()
  
  if (textLower.includes(queryLower)) return true
  
  const textWords = textLower.split(/\s+/)
  const queryWords = queryLower.split(/\s+/)
  
  for (const qWord of queryWords) {
    const qStem = stem(qWord)
    
    for (const tWord of textWords) {
      const tStem = stem(tWord)
      
      if (qStem.length >= 3 && tStem.startsWith(qStem)) return true
      if (tStem.length >= 3 && qStem.startsWith(tStem)) return true
      
      if (qWord.length >= 4 && tWord.length >= 4) {
        const dist = levenshtein(qWord, tWord)
        const maxDist = Math.floor(Math.max(qWord.length, tWord.length) * 0.3)
        if (dist <= maxDist && dist <= 2) return true
      }
      
      if (qStem.length >= 3 && tStem.length >= 3) {
        const dist = levenshtein(qStem, tStem)
        if (dist <= 1) return true
      }
    }
  }
  
  return false
}

// Подсветка
const highlightText = (text: string, query: string) => {
  if (!query || !text) return text
  
  const words = text.split(/(\s+|[.,;:!?()«»])/g)
  const queryLower = query.toLowerCase()
  const queryStem = stem(queryLower)
  
  return words.map((word, i) => {
    if (/^\s+$/.test(word) || /^[.,;:!?()«»]+$/.test(word)) {
      return <span key={i}>{word}</span>
    }
    
    const wordLower = word.toLowerCase()
    const wordStem = stem(wordLower)
    
    if (wordLower.includes(queryLower)) {
      return <strong key={i}>{word}</strong>
    }
    
    if (queryStem.length >= 3 && (wordStem.startsWith(queryStem) || queryStem.startsWith(wordStem))) {
      return <strong key={i}>{word}</strong>
    }
    
    if (queryLower.length >= 4 && wordLower.length >= 4) {
      const dist = levenshtein(queryLower, wordLower)
      const maxDist = Math.floor(Math.max(queryLower.length, wordLower.length) * 0.3)
      if (dist <= maxDist && dist <= 2) {
        return <strong key={i}>{word}</strong>
      }
    }
    
    if (queryStem.length >= 3 && wordStem.length >= 3) {
      const dist = levenshtein(queryStem, wordStem)
      if (dist <= 1) {
        return <strong key={i}>{word}</strong>
      }
    }
    
    return <span key={i}>{word}</span>
  })
}

export default function HomePage() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [displayedSuppliers, setDisplayedSuppliers] = useState<Supplier[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [tagSuggestions, setTagSuggestions] = useState<SearchSuggestion[]>([])
  const [categorySuggestions, setCategorySuggestions] = useState<SearchSuggestion[]>([])
  const searchTimeoutRef = useRef<NodeJS.Timeout>()
  const searchRef = useRef<HTMLDivElement>(null)
  const [userRole, setUserRole] = useState<string>('')
  const [selectedProduct, setSelectedProduct] = useState<SearchSuggestion | null>(null)
  
  const [showAllResultsModal, setShowAllResultsModal] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [selectedSuppliers, setSelectedSuppliers] = useState<string[]>([])
  const [emailSubject, setEmailSubject] = useState('')
  const [emailBody, setEmailBody] = useState('')
  const [attachments, setAttachments] = useState<File[]>([])
  const [sending, setSending] = useState(false)
  const [sendProgress, setSendProgress] = useState(0)

  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    if (!token) { router.push('/login'); return }
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    setUserRole(user?.role || '')
    fetchSuppliers()
  }

  const fetchSuppliers = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }
      const data = await response.json()
      setSuppliers(data.suppliers || [])
      setDisplayedSuppliers(data.suppliers || [])
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const performSearch = async (query: string) => {
    if (!query || query.length < 2) {
      setSuggestions([])
      setTagSuggestions([])
      setCategorySuggestions([])
      setShowSuggestions(false)
      return
    }

    setSearching(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_URL}/api/suppliers/search?q=${encodeURIComponent(query)}&limit=100`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (response.ok) {
        const data = await response.json()
        
        // Парсим теги (приоритет 1)
        const tags = data.top_tags || []
        const tagSuggestions: SearchSuggestion[] = tags.slice(0, 5).map((t: any) => ({
          type: 'tag',
          name: t.tag,
          count: t.count
        }))
        setTagSuggestions(tagSuggestions)
        
        // Товары
        const allProducts = data.all_products || []
        const productSuggestions: SearchSuggestion[] = []
        const seenProducts = new Set<string>()        
        // Категории - переводим ключи в названия
        const catSuggestions: SearchSuggestion[] = []
        const categoryMap: Record<string, string> = {}
        
        // Загружаем маппинг категорий
        try {
          const catResponse = await fetch(`${API_URL}/api/suppliers/categories`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (catResponse.ok) {
            const catData = await catResponse.json()
            Object.entries(catData.categories || {}).forEach(([key, value]: [string, any]) => {
              categoryMap[key] = value.name
            })
          }
        } catch (e) {
          console.error('Failed to load category names:', e)
        }
        
        const categoryCount = new Map<string, number>()
        data.results.forEach((result: any) => {
          if (result.supplier_categories) {
            result.supplier_categories.forEach((catKey: string) => {
              const catName = categoryMap[catKey] || catKey
              categoryCount.set(catName, (categoryCount.get(catName) || 0) + 1)
            })
          }
        })
        
        categoryCount.forEach((count, name) => {
          catSuggestions.push({
            type: 'category',
            name: name,
            count: count
          })
        })
        
        setCategorySuggestions(catSuggestions.slice(0, 5))
        
        allProducts.forEach((product: any) => {
          const key = `${product.sku || ''}_${product.name}`
          if (!seenProducts.has(key)) {
            seenProducts.add(key)
            
            const supplier = data.results.find((r: any) => r.supplier_id === product.supplier_id)
            
            productSuggestions.push({
              type: 'product',
              name: product.name,
              sku: product.sku,
              supplier_id: product.supplier_id,
              supplier_name: supplier?.supplier_name || '',
              score: product.score || 0
            })
          }
        })
        
        setSuggestions(productSuggestions)
        setShowSuggestions(true)
      }
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setSearching(false)
    }
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    setSelectedProduct(null)

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (value.length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(value)
      }, 500)
    } else {
      setSuggestions([])
      setTagSuggestions([])
      setCategorySuggestions([])
      setShowSuggestions(false)
      setDisplayedSuppliers(suppliers)
    }
  }

  const handleSelectSuggestion = async (suggestion: SearchSuggestion) => {
    setSelectedProduct(suggestion)
    
    if (suggestion.type === 'tag') {
      // Для тега - показываем всех поставщиков с товарами содержащими этот тег
      setSearchQuery(suggestion.name)
    } else if (suggestion.type === 'product') {
      setSearchQuery(suggestion.sku ? `${suggestion.sku} - ${suggestion.name}` : suggestion.name)
    } else {
      setSearchQuery(suggestion.name)
    }
    
    setShowSuggestions(false)
    setShowAllResultsModal(false)

    try {
      const token = localStorage.getItem('access_token')
      const searchTerm = suggestion.type === 'tag' ? suggestion.name : (suggestion.sku || suggestion.name)
      const response = await fetch(
        `${API_URL}/api/suppliers/search?q=${encodeURIComponent(searchTerm)}&limit=100`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (response.ok) {
        const data = await response.json()
        const supplierIds = new Set(data.results.map((r: any) => r.supplier_id))
        const filtered = suppliers.filter(s => supplierIds.has(s.id))
        setDisplayedSuppliers(filtered)
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const openEmailModal = () => {
    const availableSuppliers = displayedSuppliers.filter(
      s => s.email && s.status === 'ACTIVE' && !s.is_blacklisted
    )
    setSelectedSuppliers(availableSuppliers.map(s => s.id))
    setEmailSubject('')
    setEmailBody('')
    setAttachments([])
    setShowEmailModal(true)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      const validFiles = newFiles.filter(f => f.size <= 100 * 1024 * 1024)
      
      if (validFiles.length < newFiles.length) {
        alert('Некоторые файлы превышают лимит в 100MB')
      }
      
      setAttachments(prev => [...prev, ...validFiles])
    }
  }

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  const toggleSupplier = (supplierId: string) => {
    setSelectedSuppliers(prev =>
      prev.includes(supplierId)
        ? prev.filter(id => id !== supplierId)
        : [...prev, supplierId]
    )
  }

  const sendPriceRequests = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) {
      alert('Заполните тему и текст письма')
      return
    }

    if (selectedSuppliers.length === 0) {
      alert('Выберите хотя бы одного поставщика')
      return
    }

    setSending(true)
    setSendProgress(0)

    try {
      const token = localStorage.getItem('access_token')
      let sentCount = 0
      let failedCount = 0

      for (let i = 0; i < selectedSuppliers.length; i++) {
        const supplierId = selectedSuppliers[i]
        const supplier = suppliers.find(s => s.id === supplierId)
        
        if (!supplier?.email) continue

        const formData = new FormData()
        formData.append('to', supplier.email)
        formData.append('subject', emailSubject)
        formData.append('body', emailBody)

        attachments.forEach(file => {
          formData.append('files', file)
        })

        try {
          const response = await fetch(`${API_URL}/api/mail/send`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
          })

          if (response.ok) sentCount++
          else failedCount++
        } catch {
          failedCount++
        }

        setSendProgress(Math.round(((i + 1) / selectedSuppliers.length) * 100))
      }

      setTimeout(() => {
        setShowEmailModal(false)
        setSending(false)
        setSendProgress(0)
        alert(`Отправка завершена:\n✓ Успешно: ${sentCount}\n✗ Ошибок: ${failedCount}`)
        
        setSelectedProduct(null)
        setSearchQuery('')
        setDisplayedSuppliers(suppliers)
      }, 500)

    } catch (error) {
      console.error('Error:', error)
      alert('Ошибка при отправке писем')
      setSending(false)
      setSendProgress(0)
    }
  }

  const availableEmailSuppliers = displayedSuppliers.filter(
    s => s.email && s.status === 'ACTIVE' && !s.is_blacklisted
  )

  const totalSuggestions = tagSuggestions.length + suggestions.length + categorySuggestions.length

  return (
    <LayoutWithSidebar>
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative" ref={searchRef}>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Поиск товаров, артикулов, категорий... (мин. 2 символа)"
                  className="w-full px-4 py-2 pr-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onFocus={() => totalSuggestions > 0 && setShowSuggestions(true)}
                />
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              </div>

              {showSuggestions && totalSuggestions > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-96 overflow-hidden flex flex-col">
                  <div className="flex-1 overflow-y-auto p-2">
                    
                    {/* ТЕГИ - ПРИОРИТЕТ 1 */}
                    {tagSuggestions.length > 0 && (
                      <>
                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase bg-green-50">
                          🏷️ Популярные теги ({tagSuggestions.length})
                        </div>
                        {tagSuggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSelectSuggestion(suggestion)}
                            className="w-full text-left px-3 py-2 hover:bg-green-50 rounded flex items-center justify-between border-l-2 border-green-500"
                          >
                            <span className="text-sm font-medium text-green-700">
                              {highlightText(suggestion.name, searchQuery)}
                            </span>
                            {suggestion.count && (
                              <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded font-semibold">
                                {suggestion.count} товаров
                              </span>
                            )}
                          </button>
                        ))}
                      </>
                    )}

                    {/* КАТЕГОРИИ - ПРИОРИТЕТ 2 */}
                    {categorySuggestions.length > 0 && (
                      <>
                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase mt-2">
                          Категории
                        </div>
                        {categorySuggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSelectSuggestion(suggestion)}
                            className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded flex items-center justify-between"
                          >
                            <span className="text-sm">{suggestion.name}</span>
                            {suggestion.count && (
                              <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                                {suggestion.count}
                              </span>
                            )}
                          </button>
                        ))}
                      </>
                    )}

                    {/* ТОВАРЫ - ПРИОРИТЕТ 3 */}
                    {suggestions.length > 0 && (
                      <>
                        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase mt-2">
                          Конкретные товары ({suggestions.length})
                        </div>
                        {suggestions.slice(0, 5).map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSelectSuggestion(suggestion)}
                            className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded flex items-center space-x-2"
                          >
                            <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm truncate">
                                {highlightText(suggestion.name, searchQuery)}
                              </div>
                              {suggestion.sku && (
                                <div className="text-xs text-gray-500 font-mono">
                                  {highlightText(suggestion.sku, searchQuery)}
                                </div>
                              )}
                            </div>
                          </button>
                        ))}
                      </>
                    )}
                  </div>

                  <div className="border-t p-2 flex justify-center">
                    <button
                      onClick={() => {
                        setShowSuggestions(false)
                        setShowAllResultsModal(true)
                      }}
                      className="flex-1 px-3 py-2 text-sm text-center text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Посмотреть все ({totalSuggestions})
                    </button>
                  </div>
                </div>
              )}

              {searching && (
                <div className="absolute right-12 top-1/2 transform -translate-y-1/2">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                </div>
              )}
            </div>

            {userRole === 'admin' && (
              <button
                onClick={() => router.push('/suppliers/add')}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Добавить поставщика
              </button>
            )}
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="text-sm text-gray-600">
              {selectedProduct ? (
                <span>Найдено поставщиков: {displayedSuppliers.length}</span>
              ) : (
                <span>Всего поставщиков: {suppliers.length}</span>
              )}
            </div>

            {selectedProduct && displayedSuppliers.length > 0 && (
              <button
                onClick={openEmailModal}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                <Mail className="w-4 h-4" />
                <span>Отправить запрос цен</span>
              </button>
            )}
          </div>
        </header>

        <div className="p-8">
          <h1 className="text-2xl font-bold mb-6">
            {selectedProduct ? `Поставщики: ${selectedProduct.name}` : 'Все поставщики'}
          </h1>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : displayedSuppliers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {selectedProduct ? 'Поставщики не найдены' : 'Нет поставщиков'}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedSuppliers.map(supplier => (
                <div
                  key={supplier.id}
                  onClick={() => router.push(`/suppliers/${supplier.id}`)}
                  className="bg-white rounded-lg border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition cursor-pointer p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{supplier.name}</h3>
                      <p className="text-sm text-gray-500">ИНН: {supplier.inn}</p>
                    </div>
                    <div className="flex items-center space-x-1 ml-2">
                      <span className="text-yellow-500">★</span>
                      <span className="text-sm font-medium">
                        {supplier.rating ? supplier.rating.toFixed(1) : '0.0'}
                      </span>
                    </div>
                  </div>

                  {supplier.tags_array && supplier.tags_array.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {supplier.tags_array.slice(0, 3).map((tag, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {showAllResultsModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-4 border-b flex items-center justify-between">
                <h2 className="text-xl font-bold">Результаты поиска: "{searchQuery}" ({totalSuggestions})</h2>
                <button onClick={() => setShowAllResultsModal(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {/* ТЕГИ */}
                {tagSuggestions.length > 0 && (
                  <>
                    <h3 className="font-semibold mb-3 text-green-700">🏷️ Теги ({tagSuggestions.length})</h3>
                    <div className="space-y-2 mb-6">
                      {tagSuggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSelectSuggestion(suggestion)}
                          className="w-full text-left p-3 border-2 border-green-200 rounded-lg hover:bg-green-50 hover:border-green-400 transition flex justify-between items-center"
                        >
                          <span className="font-medium text-green-700">{highlightText(suggestion.name, searchQuery)}</span>
                          <span className="text-sm text-green-600 bg-green-100 px-2 py-1 rounded font-semibold">
                            {suggestion.count} товаров
                          </span>
                        </button>
                      ))}
                    </div>
                  </>
                )}

                {/* КАТЕГОРИИ */}
                {categorySuggestions.length > 0 && (
                  <>
                    <h3 className="font-semibold mb-3">Категории</h3>
                    <div className="space-y-2 mb-6">
                      {categorySuggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSelectSuggestion(suggestion)}
                          className="w-full text-left p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition flex justify-between items-center"
                        >
                          <span>{suggestion.name}</span>
                          <span className="text-sm text-gray-500 bg-gray-200 px-2 py-1 rounded">
                            {suggestion.count} товаров
                          </span>
                        </button>
                      ))}
                    </div>
                  </>
                )}

                {/* ТОВАРЫ */}
                {suggestions.length > 0 && (
                  <>
                    <h3 className="font-semibold mb-3">Товары ({suggestions.length})</h3>
                    <div className="space-y-2">
                      {suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSelectSuggestion(suggestion)}
                          className="w-full text-left p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition"
                        >
                          <div className="font-medium">{highlightText(suggestion.name, searchQuery)}</div>
                          {suggestion.sku && (
                            <div className="text-sm text-gray-500 font-mono mt-1">
                              Артикул: {highlightText(suggestion.sku, searchQuery)}
                            </div>
                          )}
                          {suggestion.supplier_name && (
                            <div className="text-xs text-gray-400 mt-1">
                              Поставщик: {suggestion.supplier_name}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {showEmailModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-4 border-b flex items-center justify-between">
                <h2 className="text-xl font-bold">Отправка запроса цен</h2>
                <button onClick={() => !sending && setShowEmailModal(false)} disabled={sending}>
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 flex-1 overflow-y-auto space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Тема письма *</label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="Запрос цен на товар"
                    disabled={sending}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Текст письма *</label>
                  <textarea
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    rows={8}
                    className="w-full px-3 py-2 border rounded-lg resize-none"
                    placeholder="Здравствуйте!&#10;&#10;Просим предоставить коммерческое предложение..."
                    disabled={sending}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Вложения (до 100MB каждый)</label>
                  <input
                    type="file"
                    onChange={handleFileSelect}
                    multiple
                    className="hidden"
                    id="file-upload"
                    disabled={sending}
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg cursor-pointer text-sm"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Прикрепить файлы
                  </label>

                  {attachments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {attachments.map((file, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span className="text-sm truncate">{file.name}</span>
                            <span className="text-xs text-gray-400 flex-shrink-0">
                              ({(file.size / 1024 / 1024).toFixed(2)} MB)
                            </span>
                          </div>
                          <button
                            onClick={() => removeAttachment(idx)}
                            className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                            disabled={sending}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="font-semibold mb-3">
                    Получатели ({selectedSuppliers.length} выбрано)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-60 overflow-y-auto border rounded-lg p-2">
                    {availableEmailSuppliers.map(supplier => (
                      <label
                        key={supplier.id}
                        className={`flex items-center space-x-3 p-3 rounded cursor-pointer border-2 transition ${
                          selectedSuppliers.includes(supplier.id)
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSuppliers.includes(supplier.id)}
                          onChange={() => toggleSupplier(supplier.id)}
                          className="w-4 h-4"
                          disabled={sending}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{supplier.name}</div>
                          <div className="text-xs text-gray-500 truncate">{supplier.email}</div>
                        </div>
                        <div className="flex items-center space-x-1 flex-shrink-0">
                          <span className="text-yellow-500 text-sm">★</span>
                          <span className="text-xs">{supplier.rating?.toFixed(1) || '0.0'}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {sending && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Отправка...</span>
                      <span>{sendProgress}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 transition-all"
                        style={{ width: `${sendProgress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-t flex justify-end space-x-3">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                  disabled={sending}
                >
                  Отмена
                </button>
                <button
                  onClick={sendPriceRequests}
                  disabled={sending || selectedSuppliers.length === 0}
                  className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 flex items-center space-x-2"
                >
                  {sending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Отправка...</span>
                    </>
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      <span>Отправить ({selectedSuppliers.length})</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </LayoutWithSidebar>
  )
}
