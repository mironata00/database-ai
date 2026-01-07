'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from './layout-with-sidebar'
import { Search, Loader2, Mail, X, Check, Filter } from 'lucide-react'

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

interface ProductItem {
  name: string
  sku: string | null
}

export default function HomePage() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()
  const [userRole, setUserRole] = useState<string>('')
  const [categories, setCategories] = useState<any>({})
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [useCategoryColors, setUseCategoryColors] = useState(true)

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set())
  const [availableProducts, setAvailableProducts] = useState<ProductItem[]>([])
  const [selectedSuppliers, setSelectedSuppliers] = useState<string[]>([])
  const [emailSubject, setEmailSubject] = useState('')
  const [emailBody, setEmailBody] = useState('')
  const [sending, setSending] = useState(false)
  const [sendProgress, setSendProgress] = useState(0)

  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    if (!token) { router.push('/login'); return }
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    setUserRole(user?.role || '')
    fetchCategories()
    fetchSuppliers()
    fetchDefaults()
  }

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/suppliers/categories`)
      if (response.ok) {
        const data = await response.json()
        setCategories(data.categories || {})
        setUseCategoryColors(data.use_category_colors || false)
      }
    } catch (error) {
      console.error('Error:', error)
    }
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
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchDefaults = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/price-requests/defaults`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setEmailSubject(data.subject)
        setEmailBody(data.body)
      }
    } catch (error) {
      console.error('Error fetching defaults:', error)
    }
  }

  const performSearch = async (query: string) => {
    if (!query || query.length < 2) {
      setSearchResults([])
      return
    }

    setSearching(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${API_URL}/api/suppliers/search?q=${encodeURIComponent(query)}&limit=50`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
      }
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setSearching(false)
    }
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (value.length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(value)
      }, 300)
    } else {
      setSearchResults([])
    }
  }

  const handleSupplierClick = (supplierId: string) => {
    router.push(`/suppliers/${supplierId}`)
  }

  const openPriceRequestModal = () => {
    const products: ProductItem[] = []
    const seen = new Set<string>()

    const currentResults = getDisplayedSuppliers()

    currentResults.forEach((result: any) => {
      if (result._search?.example_products) {
        result._search.example_products.forEach((p: any) => {
          const key = `${p.name}_${p.sku || ''}`
          if (!seen.has(key) && products.length < 20) {
            seen.add(key)
            products.push({ name: p.name, sku: p.sku })
          }
        })
      }
    })

    setAvailableProducts(products)

    const productKeys = new Set(products.map(p => `${p.name}_${p.sku || ''}`))
    setSelectedProducts(productKeys)

    const supplierIds = currentResults
      .filter((s: any) => {
        const fullSupplier = suppliers.find(sup => sup.id === s.id)
        return fullSupplier?.email && fullSupplier?.status === 'ACTIVE' && !fullSupplier?.is_blacklisted
      })
      .sort((a: any, b: any) => (b.rating || 0) - (a.rating || 0))
      .map((s: any) => s.id)

    setSelectedSuppliers(supplierIds)
    setShowModal(true)
  }

  const toggleProduct = (product: ProductItem) => {
    const key = `${product.name}_${product.sku || ''}`
    setSelectedProducts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  const toggleSupplier = (supplierId: string) => {
    setSelectedSuppliers(prev =>
      prev.includes(supplierId)
        ? prev.filter(id => id !== supplierId)
        : [...prev, supplierId]
    )
  }

  const sendPriceRequests = async () => {
    const productsToSend = availableProducts.filter(p =>
      selectedProducts.has(`${p.name}_${p.sku || ''}`)
    )

    if (productsToSend.length === 0) {
      alert('Выберите хотя бы один товар')
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

      const progressInterval = setInterval(() => {
        setSendProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      const response = await fetch(`${API_URL}/api/price-requests/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          products: productsToSend,
          supplier_ids: selectedSuppliers,
          subject: emailSubject,
          body: emailBody
        })
      })

      clearInterval(progressInterval)
      setSendProgress(100)

      if (response.ok) {
        const data = await response.json()
        setTimeout(() => {
          setShowModal(false)
          setSending(false)
          setSendProgress(0)
          alert(`Запросы отправлены: ${data.sent_count} успешно, ${data.failed_count} ошибок`)
        }, 500)
      } else {
        throw new Error('Ошибка отправки')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Ошибка при отправке запросов')
      setSending(false)
      setSendProgress(0)
    }
  }

  const getDisplayedSuppliers = () => {
    let results = searchQuery.length >= 2
      ? searchResults.map(result => ({
          id: result.supplier_id,
          name: result.supplier_name,
          inn: result.supplier_inn,
          status: result.supplier_status,
          rating: result.supplier_rating,
          email: null,
          is_blacklisted: false,
          tags_array: result.supplier_tags || [],
          color: result.supplier_color || '#3B82F6',
          categories: result.supplier_categories || [],
          _search: {
            matched_products: result.matched_products,
            example_products: result.example_products
          }
        }))
      : suppliers

    if (selectedCategory) {
      results = results.filter((s: any) => s.categories && s.categories.includes(selectedCategory))
    }

    return results
  }

  const displayedSuppliers = getDisplayedSuppliers()

  const availableSuppliers = suppliers
    .filter(s => s.email && s.status === 'ACTIVE' && !s.is_blacklisted)
    .sort((a, b) => (b.rating || 0) - (a.rating || 0))

  return (
    <LayoutWithSidebar>
      <main className="flex-1 overflow-auto">
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Поиск по названию, артикулу, бренду, категории... (мин. 2 символа)"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 animate-spin text-blue-500" />
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

          {/* Счетчик и кнопка запроса цен */}
          <div className="flex items-center justify-between mt-3">
            {searchQuery.length >= 2 ? (
              <div className="text-sm text-gray-600">
                {searching ? 'Поиск...' : `Найдено: ${displayedSuppliers.length}${selectedCategory ? ` (отфильтровано по категории)` : ''}`}
              </div>
            ) : (
              <div className="text-sm text-gray-600">
                Показано: {displayedSuppliers.length} из {suppliers.length}
              </div>
            )}

            {searchQuery.length >= 2 && displayedSuppliers.length > 0 && (
              <button
                onClick={openPriceRequestModal}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                <Mail className="w-4 h-4" />
                <span>Отправить запрос цен</span>
              </button>
            )}
          </div>

          {/* Фильтр по категориям */}
          {Object.keys(categories).length > 0 && (
            <div className="mt-2 flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-1.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все направления</option>
                {Object.entries(categories).map(([key, value]: [string, any]) => (
                  <option key={key} value={key}>{value.name}</option>
                ))}
              </select>
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory('')}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Сбросить
                </button>
              )}
            </div>
          )}
        </header>

        <div className="p-8">
          <h1 className="text-2xl font-bold mb-6">Список поставщиков</h1>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                <div className="text-gray-500">Загрузка...</div>
              </div>
            </div>
          ) : displayedSuppliers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchQuery.length >= 2 
                ? (selectedCategory ? 'В этой категории ничего не найдено' : 'Ничего не найдено')
                : (selectedCategory ? 'В этой категории нет поставщиков' : 'Поставщики не найдены')
              }
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedSuppliers.map((supplier: any) => (
                <div
                  key={supplier.id}
                  onClick={() => handleSupplierClick(supplier.id)}
                  className="bg-white rounded-lg border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition cursor-pointer overflow-hidden"
                  style={useCategoryColors ? { borderLeft: `3px solid ${supplier.color || '#3B82F6'}` } : {}}
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{supplier.name}</h3>
                        <p className="text-sm text-gray-500">ИНН: {supplier.inn}</p>
                      </div>
                      <div className="flex items-center space-x-1 ml-2">
                        <span className="text-yellow-500">★</span>
                        <span className="text-sm font-medium text-gray-700">
                          {supplier.rating ? supplier.rating.toFixed(1) : '0.0'}
                        </span>
                      </div>
                    </div>

                    {supplier._search && supplier._search.matched_products > 0 && (
                      <div className="mb-2 p-2 bg-blue-50 rounded">
                        <div className="text-xs text-blue-600 font-medium">
                          Найдено товаров: {supplier._search.matched_products}
                        </div>
                        {supplier._search.example_products && supplier._search.example_products.length > 0 && (
                          <div className="mt-1 space-y-1">
                            {supplier._search.example_products.slice(0, 2).map((product: any, idx: number) => (
                              <div key={idx} className="text-xs text-gray-600 truncate">
                                {product.sku && <span className="font-mono text-gray-500">{product.sku}</span>}
                                {product.name && <span className="ml-1">{product.name.substring(0, 40)}...</span>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {supplier.tags_array && supplier.tags_array.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {supplier.tags_array.slice(0, 3).map((tag: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                        {supplier.tags_array.length > 3 && (
                          <span className="text-xs text-gray-500">+{supplier.tags_array.length - 3}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal */}
        {showModal && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={(e) => {
              if (e.target === e.currentTarget && !sending) setShowModal(false)
            }}
          >
            <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between z-10">
                <h2 className="text-xl font-bold">Отправка запроса цен</h2>
                <button
                  onClick={() => !sending && setShowModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                  disabled={sending}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                <div>
                  <h3 className="font-semibold mb-3">Найденные товары ({availableProducts.length})</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                    {availableProducts.map((product, idx) => {
                      const key = `${product.name}_${product.sku || ''}`
                      const isSelected = selectedProducts.has(key)
                      return (
                        <div
                          key={idx}
                          onClick={() => toggleProduct(product)}
                          className={`flex items-start space-x-2 p-3 rounded cursor-pointer border-2 transition ${
                            isSelected
                              ? 'bg-green-50 border-green-500'
                              : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex-shrink-0 mt-0.5">
                            {isSelected ? (
                              <Check className="w-5 h-5 text-green-600" />
                            ) : (
                              <div className="w-5 h-5 border-2 border-gray-300 rounded" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{product.name}</div>
                            {product.sku && (
                              <div className="text-xs text-gray-500 font-mono">{product.sku}</div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Тема письма</label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg"
                    disabled={sending}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Текст письма</label>
                  <textarea
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border rounded-lg resize-none"
                    disabled={sending}
                  />
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Поставщики (по рейтингу) - {availableSuppliers.length} доступно</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-80 overflow-y-auto">
                    {availableSuppliers.map(supplier => (
                      <div
                        key={supplier.id}
                        onClick={() => toggleSupplier(supplier.id)}
                        className={`flex items-center space-x-2 p-3 rounded-lg border-2 cursor-pointer transition overflow-hidden ${
                          selectedSuppliers.includes(supplier.id)
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        style={useCategoryColors ? { borderLeft: `4px solid ${supplier.color}` } : {}}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{supplier.name}</div>
                          <div className="text-xs text-gray-500 truncate">{supplier.email}</div>
                        </div>
                        <div className="flex items-center space-x-1 flex-shrink-0">
                          <span className="text-yellow-500 text-sm">★</span>
                          <span className="text-xs font-medium">{supplier.rating?.toFixed(1) || '0.0'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {sending && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Отправка...</span>
                      <span>{sendProgress}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 transition-all duration-300"
                        style={{ width: `${sendProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <div className="text-sm text-gray-600">
                    Выбрано: {selectedProducts.size} товаров, {selectedSuppliers.length} поставщиков
                  </div>
                  <button
                    onClick={sendPriceRequests}
                    disabled={sending || selectedProducts.size === 0 || selectedSuppliers.length === 0}
                    className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2"
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
          </div>
        )}
      </main>
    </LayoutWithSidebar>
  )
}
