'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../layout-with-sidebar'
import { Plus, Search, Edit, Trash2, UserCheck, UserX } from 'lucide-react'

interface Manager {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export default function ManagersPage() {
  const router = useRouter()
  const [managers, setManagers] = useState<Manager[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])
  useEffect(() => { if (!loading) { fetchManagers() } }, [roleFilter, statusFilter])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    if (!token) { router.push('/login'); return }
    const user = userData ? JSON.parse(userData) : null
    if (user?.role !== 'admin') { alert('Доступ запрещен. Только для администраторов.'); router.push('/'); return }
    fetchManagers()
  }

  const fetchManagers = async () => {
    try {
      const token = localStorage.getItem('access_token')
      let url = `${API_URL}/api/managers/?limit=100`
      
      if (roleFilter !== 'all') {
        url += `&role=${roleFilter}`
      }
      if (statusFilter !== 'all') {
        url += `&is_active=${statusFilter === 'active' ? 'true' : 'false'}`
      }

      console.log('Fetching URL:', url)
      
      const response = await fetch(url, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      })
      
      if (response.status === 401) { 
        localStorage.clear()
        router.push('/login')
        return 
      }
      if (response.status === 403) { 
        alert('Доступ запрещен')
        router.push('/')
        return 
      }
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', response.status, errorText)
        alert('Ошибка загрузки данных')
        return
      }

      const data = await response.json()
      setManagers(data.users || [])
    } catch (error) {
      console.error('Error:', error)
      alert('Ошибка соединения с сервером')
    } finally {
      setLoading(false)
    }
  }

  const deleteManager = async (id: string) => {
    if (!confirm('Вы уверены, что хотите удалить этого пользователя?')) return
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${id}`, { 
        method: 'DELETE', 
        headers: { 'Authorization': `Bearer ${token}` } 
      })
      
      if (response.ok) { 
        fetchManagers()
        alert('Пользователь удален') 
      } else { 
        const data = await response.json()
        alert(data.detail || 'Ошибка удаления') 
      }
    } catch (error) { 
      console.error('Delete error:', error)
      alert('Ошибка удаления пользователя') 
    }
  }

  const toggleStatus = async (id: string, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_active: !currentStatus })
      })
      
      if (response.ok) {
        fetchManagers()
        alert(`Пользователь ${!currentStatus ? 'активирован' : 'деактивирован'}`)
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка изменения статуса')
      }
    } catch (error) {
      console.error('Toggle status error:', error)
      alert('Ошибка изменения статуса')
    }
  }

  const filteredManagers = managers.filter(m => {
    const q = searchQuery.toLowerCase()
    return m.email.toLowerCase().includes(q) || (m.full_name?.toLowerCase() || '').includes(q)
  })

  const getRoleBadge = (role: string) => {
    const colors: Record<string, string> = {
      admin: 'bg-purple-100 text-purple-700',
      manager: 'bg-blue-100 text-blue-700',
      viewer: 'bg-gray-100 text-gray-700'
    }
    const labels: Record<string, string> = {
      admin: 'Администратор',
      manager: 'Менеджер',
      viewer: 'Наблюдатель'
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[role] || colors.viewer}`}>
        {labels[role] || role}
      </span>
    )
  }

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-semibold">Управление пользователями</h1>
              <button 
                onClick={() => router.push('/managers/add')} 
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Добавить пользователя</span>
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input 
                    type="text" 
                    placeholder="Поиск по email или имени..." 
                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    value={searchQuery} 
                    onChange={(e) => setSearchQuery(e.target.value)} 
                  />
                </div>
              </div>
              <select 
                value={roleFilter} 
                onChange={(e) => setRoleFilter(e.target.value)} 
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Все роли</option>
                <option value="admin">Администраторы</option>
                <option value="manager">Менеджеры</option>
                <option value="viewer">Наблюдатели</option>
              </select>
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)} 
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Все статусы</option>
                <option value="active">Активные</option>
                <option value="inactive">Неактивные</option>
              </select>
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
          ) : filteredManagers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Пользователи не найдены
            </div>
          ) : (
            <div className="bg-white rounded-lg border overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Создан</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredManagers.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                            {m.full_name?.charAt(0) || m.email.charAt(0).toUpperCase()}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{m.full_name || 'Без имени'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{m.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">{getRoleBadge(m.role)}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          m.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {m.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(m.created_at).toLocaleDateString('ru')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button 
                            onClick={() => router.push(`/managers/${m.id}`)} 
                            className="text-blue-600 hover:text-blue-900 p-2 hover:bg-blue-50 rounded" 
                            title="Редактировать"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => toggleStatus(m.id, m.is_active)} 
                            className={`p-2 rounded ${
                              m.is_active 
                                ? 'text-orange-600 hover:text-orange-900 hover:bg-orange-50' 
                                : 'text-green-600 hover:text-green-900 hover:bg-green-50'
                            }`}
                            title={m.is_active ? 'Деактивировать' : 'Активировать'}
                          >
                            {m.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                          </button>
                          <button 
                            onClick={() => deleteManager(m.id)} 
                            className="text-red-600 hover:text-red-900 p-2 hover:bg-red-50 rounded" 
                            title="Удалить"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!loading && filteredManagers.length > 0 && (
            <div className="mt-4 text-sm text-gray-500 text-center">
              Найдено: {filteredManagers.length} из {managers.length}
            </div>
          )}
        </div>
      </div>
    </LayoutWithSidebar>
  )
}
