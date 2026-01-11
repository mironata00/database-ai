'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../layout-with-sidebar'
import { Plus, Search, Edit, Trash2, Star } from 'lucide-react'

interface Supplier {
  id: string
  name: string
  inn: string
  email: string | null
  contact_email: string | null
  phone: string | null
  contact_person: string | null
  color: string
  status: string
  rating: number | null
  is_blacklisted: boolean
  created_at: string
}

export default function SuppliersPage() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [useCategoryColors, setUseCategoryColors] = useState(true)
  const [userRole, setUserRole] = useState<string>('')
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    if (!token) { router.push('/login'); return }
    const userData = localStorage.getItem('user')
    const user = userData ? JSON.parse(userData) : null
    setUserRole(user?.role || '')
    fetchCategorySettings()
    fetchSuppliers()
  }

  const fetchCategorySettings = async () => {
    try {
      const response = await fetch(`${API_URL}/api/suppliers/categories`)
      if (response.ok) {
        const data = await response.json()
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
      
      if (response.ok) {
        const data = await response.json()
        setSuppliers(data.suppliers || [])
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteSupplier = async (id: string, name: string) => {
    if (!confirm(`Вы уверены, что хотите удалить поставщика "${name}"?`)) return
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        fetchSuppliers()
        alert('Поставщик удален')
      } else {
        alert('Ошибка удаления')
      }
    } catch (error) {
      console.error('Delete error:', error)
      alert('Ошибка удаления поставщика')
    }
  }

	const filteredSuppliers = suppliers.filter(s => {
    const q = searchQuery.toLowerCase()
    return s.name.toLowerCase().includes(q) || 
           s.inn.includes(q) || 
           (s.contact_email?.toLowerCase() || '').includes(q)
  })

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-semibold">База поставщиков</h1>
              {userRole === 'admin' && (
                <button
                  onClick={() => router.push('/suppliers/add')}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Добавить поставщика</span>
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Поиск по названию, ИНН или email..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-8">
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
            <div className="bg-white rounded-lg border overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Поставщик</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ИНН</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Контакты</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Рейтинг</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredSuppliers.map((supplier) => (
                    <tr key={supplier.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div
                            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold"
                            style={useCategoryColors ? { backgroundColor: supplier.color } : { backgroundColor: '#6B7280' }}
                          >
                            {supplier.name.charAt(0)}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                            <div className="text-xs text-gray-500">{supplier.contact_person || 'Контакт не указан'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{supplier.inn}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{supplier.contact_email || '-'}</div>
                        <div className="text-xs text-gray-500">{supplier.phone || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          supplier.is_blacklisted
                            ? 'bg-red-100 text-red-800'
                            : supplier.status === 'ACTIVE'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {supplier.is_blacklisted ? 'Черный список' : supplier.status === 'ACTIVE' ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {supplier.rating ? (
                          <div className="flex items-center">
                            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400 mr-1" />
                            <span className="text-sm font-medium">{supplier.rating.toFixed(1)}</span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">Нет оценок</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {userRole === 'admin' ? (
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => router.push(`/suppliers/${supplier.id}`)}
                              className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded"
                              title="Редактировать"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteSupplier(supplier.id, supplier.name)}
                              className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded"
                              title="Удалить"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => router.push(`/suppliers/${supplier.id}`)}
                            className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded"
                            title="Просмотр"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!loading && filteredSuppliers.length > 0 && (
            <div className="mt-4 text-sm text-gray-500 text-center">
              Найдено: {filteredSuppliers.length} из {suppliers.length}
            </div>
          )}
        </div>
      </div>
    </LayoutWithSidebar>
  )
}