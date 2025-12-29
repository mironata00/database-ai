'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Users, Bell, Upload, LogOut, UserCog, Loader2 } from 'lucide-react'

interface Supplier {
  id: string
  name: string
  inn: string
  email: string | null
  rating: number | null
  is_blacklisted: boolean
  tags_array: string[]
  status: string
}

interface User {
  id: string
  email: string
  full_name: string
  role: string
}

export default function HomePage() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()
  
  const API_URL = typeof window !== 'undefined' ? `http://${window.location.hostname}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    if (!token) { router.push('/login'); return }
    if (userData) { setUser(JSON.parse(userData)) }
    fetchSuppliers()
  }

  const fetchSuppliers = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/`, { headers: { 'Authorization': `Bearer ${token}` } })
      if (response.status === 401) { localStorage.clear(); router.push('/login'); return }
      const data = await response.json()
      setSuppliers(data.suppliers || [])
    } catch (error) { console.error('Error:', error) } finally { setLoading(false) }
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

  const handleLogout = () => { localStorage.clear(); router.push('/login') }
  const handleSupplierClick = (supplierId: string) => { router.push(`/suppliers/${supplierId}`) }

  const displayedSuppliers = searchQuery.length >= 2 
    ? searchResults.map(result => ({
        id: result.supplier_id,
        name: result.supplier_name,
        inn: result.supplier_inn,
        status: result.supplier_status,
        rating: result.supplier_rating,
        email: null,
        is_blacklisted: false,
        tags_array: result.supplier_tags || [],
        _search: {
          matched_products: result.matched_products,
          example_products: result.example_products
        }
      }))
    : suppliers

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">DB</div>
            <div><h1 className="font-semibold">DataBase AI</h1></div>
          </div>
        </div>
        {user && (
          <div className="px-6 py-4 border-b border-slate-700">
            <div className="text-xs text-slate-400 mb-2">ПОЛЬЗОВАТЕЛЬ</div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-semibold">{user.full_name?.charAt(0) || 'A'}</div>
              <div className="flex-1">
                <div className="text-sm font-medium">{user.full_name}</div>
                <div className="text-xs text-slate-400 capitalize">{user.role}</div>
              </div>
            </div>
          </div>
        )}
        <nav className="flex-1 p-4 space-y-1">
          <button onClick={() => router.push('/')} className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-blue-600 text-white font-medium">
            <Search className="w-5 h-5" /><span>База поставщиков</span>
          </button>
          {user?.role === 'admin' && (
            <button onClick={() => router.push('/managers')} className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300">
              <UserCog className="w-5 h-5" /><span>Менеджеры</span>
            </button>
          )}
          <button onClick={() => router.push('/requests')} className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300">
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5" /><span>Заявки на проверку</span>
            </div>
            <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">1</span>
          </button>
          <button onClick={() => alert('Функция в разработке')} className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300">
            <Upload className="w-5 h-5" /><span>Импорт / AI Parse</span>
          </button>
        </nav>
        <div className="p-4 border-t border-slate-700">
          <button onClick={handleLogout} className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300">
            <LogOut className="w-5 h-5" /><span>Выйти</span>
          </button>
        </div>
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
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
            <button onClick={() => router.push('/suppliers/add')} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">Добавить поставщика</button>
          </div>
          {searchQuery.length >= 2 && (
            <div className="mt-2 text-sm text-gray-600">
              {searching ? 'Поиск...' : `Найдено: ${searchResults.length}`}
            </div>
          )}
        </header>
        <div className="flex-1 overflow-auto p-8">
          <h1 className="text-2xl font-bold mb-6">Список поставщиков</h1>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center"><div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div><div className="text-gray-500">Загрузка...</div></div>
            </div>
          ) : displayedSuppliers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchQuery.length >= 2 ? 'Ничего не найдено' : 'Поставщики не найдены'}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedSuppliers.map((supplier: any) => (
                <div key={supplier.id} onClick={() => handleSupplierClick(supplier.id)} className="bg-white rounded-lg p-4 border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition cursor-pointer">
                  <div className="mb-2">
                    <h3 className="font-semibold text-gray-900">{supplier.name}</h3>
                    <p className="text-sm text-gray-500">ИНН: {supplier.inn}</p>
                  </div>
                  <div className="flex items-center space-x-1 mb-2">
                    <span className="text-yellow-500">★</span>
                    <span className="text-sm text-gray-600">{supplier.rating ? supplier.rating.toFixed(1) : '0.0'}</span>
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
                              {product.sku && <span className="font-mono">{product.sku}</span>}
                              {product.name && <span className="ml-1">{product.name.substring(0, 30)}...</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {supplier.tags_array && supplier.tags_array.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {supplier.tags_array.slice(0, 3).map((tag: string, idx: number) => (
                        <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{tag}</span>
                      ))}
                      {supplier.tags_array.length > 3 && <span className="text-xs text-gray-500">+{supplier.tags_array.length - 3}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
