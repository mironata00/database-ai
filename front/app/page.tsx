'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Users, Bell, Upload, LogOut } from 'lucide-react'

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
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)

  const API_URL = typeof window !== 'undefined' 
    ? `http://${window.location.hostname}`
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
      setUser(JSON.parse(userData))
    }

    fetchSuppliers()
  }

  const fetchSuppliers = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }

      const data = await response.json()
      setSuppliers(data.suppliers || [])
    } catch (error) {
      console.error('Error fetching suppliers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    router.push('/login')
  }

  const handleSupplierClick = (supplierId: string) => {
    router.push(`/suppliers/${supplierId}`)
  }

  const filteredSuppliers = suppliers.filter(supplier => {
    const query = searchQuery.toLowerCase()
    return (
      supplier.name.toLowerCase().includes(query) ||
      supplier.inn.includes(query) ||
      (supplier.tags_array && supplier.tags_array.some(tag => tag.toLowerCase().includes(query)))
    )
  })

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - ТЕМНЫЙ */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">
              DB
            </div>
            <div>
              <h1 className="font-semibold">DataBase AI</h1>
            </div>
          </div>
        </div>

        {/* User info */}
        {user && (
          <div className="px-6 py-4 border-b border-slate-700">
            <div className="text-xs text-slate-400 mb-2">ПОЛЬЗОВАТЕЛЬ</div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-semibold">
                {user.full_name?.charAt(0) || 'A'}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{user.full_name}</div>
                <div className="text-xs text-slate-400 capitalize">{user.role}</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <button 
            onClick={() => router.push('/')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-blue-600 text-white font-medium"
          >
            <Search className="w-5 h-5" />
            <span>База поставщиков</span>
          </button>
          
          <button 
            onClick={() => alert('Функция в разработке')}
            className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300"
          >
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5" />
              <span>Заявки на проверку</span>
            </div>
            <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">1</span>
          </button>

          <button 
            onClick={() => alert('Функция в разработке')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300"
          >
            <Upload className="w-5 h-5" />
            <span>Импорт / AI Parse</span>
          </button>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-slate-700">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300"
          >
            <LogOut className="w-5 h-5" />
            <span>Выйти</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b px-6 py-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Поиск по тегу, бренду или названию (напр. 'Knauf')"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button 
              onClick={() => router.push('/suppliers/add')}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Добавить поставщика
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          <h1 className="text-2xl font-bold mb-6">Список поставщиков</h1>
          
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                <div className="text-gray-500">Загрузка...</div>
              </div>
            </div>
          ) : filteredSuppliers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Поставщики не найдены
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSuppliers.map((supplier) => (
                <div
                  key={supplier.id}
                  onClick={() => handleSupplierClick(supplier.id)}
                  className="bg-white rounded-lg p-4 border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition cursor-pointer"
                >
                  <div className="mb-2">
                    <h3 className="font-semibold text-gray-900">{supplier.name}</h3>
                    <p className="text-sm text-gray-500">ИНН: {supplier.inn}</p>
                  </div>
                  
                  <div className="flex items-center space-x-1 mb-2">
                    <span className="text-yellow-500">★</span>
                    <span className="text-sm text-gray-600">
                      {supplier.rating ? supplier.rating.toFixed(1) : '0.0'}
                    </span>
                  </div>
                  
                  {supplier.tags_array && supplier.tags_array.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {supplier.tags_array.slice(0, 3).map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {supplier.tags_array.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{supplier.tags_array.length - 3}
                        </span>
                      )}
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
