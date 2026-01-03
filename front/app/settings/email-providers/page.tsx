'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { Plus, Edit, Trash2, Server, Check, X, ArrowLeft } from 'lucide-react'

interface EmailProvider {
  id: string
  name: string
  display_name: string
  imap_host: string
  imap_port: number
  imap_use_ssl: boolean
  smtp_host: string
  smtp_port: number
  smtp_use_tls: boolean
  description: string | null
  is_active: boolean
}

export default function EmailProvidersPage() {
  const router = useRouter()
  const [providers, setProviders] = useState<EmailProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingProvider, setEditingProvider] = useState<EmailProvider | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    imap_host: '',
    imap_port: 993,
    imap_use_ssl: true,
    smtp_host: '',
    smtp_port: 587,
    smtp_use_tls: true,
    description: '',
    is_active: true
  })

  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

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
    const user = userData ? JSON.parse(userData) : null
    if (user?.role !== 'admin') {
      alert('Доступ запрещен. Только для администраторов.')
      router.push('/')
      return
    }
    fetchProviders()
  }

  const fetchProviders = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/email-providers/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }
      
      if (response.ok) {
        const data = await response.json()
        setProviders(data)
      }
    } catch (error) {
      console.error('Error fetching providers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const token = localStorage.getItem('access_token')
      const url = editingProvider 
        ? `${API_URL}/api/email-providers/${editingProvider.id}`
        : `${API_URL}/api/email-providers/`
      
      const response = await fetch(url, {
        method: editingProvider ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        fetchProviders()
        closeModal()
      } else {
        const data = await response.json()
        setError(data.detail || 'Ошибка сохранения')
      }
    } catch (err) {
      setError('Ошибка соединения с сервером')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (name === 'custom') {
      alert('Нельзя удалить системного провайдера')
      return
    }
    
    if (!confirm('Удалить этого провайдера?')) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/email-providers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        fetchProviders()
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка удаления')
      }
    } catch (error) {
      alert('Ошибка удаления')
    }
  }

  const openAddModal = () => {
    setEditingProvider(null)
    setFormData({
      name: '',
      display_name: '',
      imap_host: '',
      imap_port: 993,
      imap_use_ssl: true,
      smtp_host: '',
      smtp_port: 587,
      smtp_use_tls: true,
      description: '',
      is_active: true
    })
    setError('')
    setShowModal(true)
  }

  const openEditModal = (provider: EmailProvider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      display_name: provider.display_name,
      imap_host: provider.imap_host,
      imap_port: provider.imap_port,
      imap_use_ssl: provider.imap_use_ssl,
      smtp_host: provider.smtp_host,
      smtp_port: provider.smtp_port,
      smtp_use_tls: provider.smtp_use_tls,
      description: provider.description || '',
      is_active: provider.is_active
    })
    setError('')
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingProvider(null)
    setError('')
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked :
              type === 'number' ? parseInt(value) || 0 : value
    }))
  }

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button onClick={() => router.push('/')} className="p-2 hover:bg-gray-100 rounded-lg">
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                  <h1 className="text-xl font-semibold">Настройки почтовых провайдеров</h1>
                  <p className="text-sm text-gray-500">Управление хостерами для IMAP/SMTP</p>
                </div>
              </div>
              <button
                onClick={openAddModal}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Добавить провайдера</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 py-8">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                <div className="text-gray-500">Загрузка...</div>
              </div>
            </div>
          ) : providers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Провайдеры не найдены
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {providers.map((provider) => (
                <div key={provider.id} className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Server className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{provider.display_name}</h3>
                        <p className="text-sm text-gray-500">{provider.name}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      provider.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {provider.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm mb-4">
                    <div className="flex justify-between">
                      <span className="text-gray-500">IMAP:</span>
                      <span className="font-mono">{provider.imap_host || '—'}:{provider.imap_port}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">SMTP:</span>
                      <span className="font-mono">{provider.smtp_host || '—'}:{provider.smtp_port}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">SSL/TLS:</span>
                      <span>
                        {provider.imap_use_ssl && <span className="text-green-600 mr-2">IMAP SSL</span>}
                        {provider.smtp_use_tls && <span className="text-green-600">SMTP TLS</span>}
                      </span>
                    </div>
                  </div>

                  {provider.description && (
                    <p className="text-sm text-gray-500 mb-4">{provider.description}</p>
                  )}

                  <div className="flex justify-end space-x-2 pt-4 border-t">
                    <button
                      onClick={() => openEditModal(provider)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                      title="Редактировать"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    {provider.name !== 'custom' && (
                      <button
                        onClick={() => handleDelete(provider.id, provider.name)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="Удалить"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">
                  {editingProvider ? 'Редактировать провайдера' : 'Добавить провайдера'}
                </h2>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                    {error}
                  </div>
                )}

                {/* Основная информация */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Системное имя <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="jino"
                      required
                      disabled={editingProvider?.name === 'custom'}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Отображаемое имя <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="display_name"
                      value={formData.display_name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="Jino.ru"
                      required
                    />
                  </div>
                </div>

                {/* IMAP настройки */}
                <div className="border rounded-lg p-4">
                  <h3 className="font-medium mb-4 text-blue-600">IMAP настройки (входящая почта)</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium mb-2">IMAP Сервер</label>
                      <input
                        type="text"
                        name="imap_host"
                        value={formData.imap_host}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="mail.jino.ru"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Порт</label>
                      <input
                        type="number"
                        name="imap_port"
                        value={formData.imap_port}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        name="imap_use_ssl"
                        checked={formData.imap_use_ssl}
                        onChange={handleChange}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm">Использовать SSL/TLS</span>
                    </label>
                  </div>
                </div>

                {/* SMTP настройки */}
                <div className="border rounded-lg p-4">
                  <h3 className="font-medium mb-4 text-green-600">SMTP настройки (исходящая почта)</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium mb-2">SMTP Сервер</label>
                      <input
                        type="text"
                        name="smtp_host"
                        value={formData.smtp_host}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="smtp.jino.ru"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Порт</label>
                      <input
                        type="number"
                        name="smtp_port"
                        value={formData.smtp_port}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        name="smtp_use_tls"
                        checked={formData.smtp_use_tls}
                        onChange={handleChange}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm">Использовать STARTTLS</span>
                    </label>
                  </div>
                </div>

                {/* Описание и статус */}
                <div>
                  <label className="block text-sm font-medium mb-2">Описание</label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Описание провайдера..."
                  />
                </div>

                <div>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleChange}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm">Провайдер активен</span>
                  </label>
                </div>

                {/* Кнопки */}
                <div className="flex justify-end space-x-4 pt-4 border-t">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                  >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </LayoutWithSidebar>
  )
}
