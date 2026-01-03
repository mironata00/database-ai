'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { ArrowLeft, Save, Key, Eye, EyeOff, Trash2, Mail, Server, Inbox } from 'lucide-react'

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
}

export default function EditManagerPage() {
  const router = useRouter()
  const params = useParams()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showSmtpPassword, setShowSmtpPassword] = useState(false)
  const [showImapPassword, setShowImapPassword] = useState(false)
  const [providers, setProviders] = useState<EmailProvider[]>([])
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    role: 'manager',
    is_active: true,
    created_at: '',
    // Провайдер
    email_provider_id: '',
    // SMTP
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_from_name: '',
    // IMAP
    imap_host: '',
    imap_port: 993,
    imap_user: '',
    imap_password: '',
    imap_use_ssl: true,
    // Шаблоны
    email_default_subject: 'Запрос цен',
    email_default_body: 'Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:',
    email_signature: 'С уважением,\nОтдел закупок'
  })
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => {
    fetchProviders()
    fetchManager()
  }, [])

  const fetchProviders = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/email-providers/short`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setProviders(data)
      }
    } catch (err) {
      console.error('Error fetching providers:', err)
    }
  }

  const fetchManager = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }

      if (response.ok) {
        const data = await response.json()
        setFormData({
          email: data.email,
          full_name: data.full_name || '',
          role: data.role,
          is_active: data.is_active,
          created_at: data.created_at || '',
          email_provider_id: data.email_provider_id || '',
          // SMTP
          smtp_host: data.smtp_host || '',
          smtp_port: data.smtp_port || 587,
          smtp_user: data.smtp_user || '',
          smtp_password: '',
          smtp_use_tls: data.smtp_use_tls !== undefined ? data.smtp_use_tls : true,
          smtp_from_name: data.smtp_from_name || '',
          // IMAP
          imap_host: data.imap_host || '',
          imap_port: data.imap_port || 993,
          imap_user: data.imap_user || '',
          imap_password: '',
          imap_use_ssl: data.imap_use_ssl !== undefined ? data.imap_use_ssl : true,
          // Шаблоны
          email_default_subject: data.email_default_subject || 'Запрос цен',
          email_default_body: data.email_default_body || 'Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:',
          email_signature: data.email_signature || 'С уважением,\nОтдел закупок'
        })
      } else {
        setError('Пользователь не найден')
      }
    } catch (error) {
      setError('Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  const handleProviderChange = (providerId: string) => {
    const provider = providers.find(p => p.id === providerId)
    if (provider && provider.name !== 'custom') {
      setFormData(prev => ({
        ...prev,
        email_provider_id: providerId,
        smtp_host: provider.smtp_host,
        smtp_port: provider.smtp_port,
        smtp_use_tls: provider.smtp_use_tls,
        imap_host: provider.imap_host,
        imap_port: provider.imap_port,
        imap_use_ssl: provider.imap_use_ssl
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        email_provider_id: providerId
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const token = localStorage.getItem('access_token')
      const payload: any = {
        email: formData.email,
        full_name: formData.full_name || null,
        role: formData.role,
        is_active: formData.is_active,
        email_provider_id: formData.email_provider_id || null,
        // SMTP
        smtp_host: formData.smtp_host || null,
        smtp_port: formData.smtp_port || 587,
        smtp_user: formData.smtp_user || null,
        smtp_use_tls: formData.smtp_use_tls,
        smtp_from_name: formData.smtp_from_name || null,
        // IMAP
        imap_host: formData.imap_host || null,
        imap_port: formData.imap_port || 993,
        imap_user: formData.imap_user || null,
        imap_use_ssl: formData.imap_use_ssl,
        // Шаблоны
        email_default_subject: formData.email_default_subject,
        email_default_body: formData.email_default_body,
        email_signature: formData.email_signature
      }

      // Добавляем пароли только если они заполнены
      if (formData.smtp_password) {
        payload.smtp_password = formData.smtp_password
      }
      if (formData.imap_password) {
        payload.imap_password = formData.imap_password
      }

      const response = await fetch(`${API_URL}/api/managers/${params.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      })

      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Ошибка обновления')
      }

      router.push('/managers')
    } catch (err: any) {
      setError(err.message || 'Ошибка обновления')
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      alert('Пароли не совпадают')
      return
    }
    if (newPassword.length < 8) {
      alert('Пароль должен содержать минимум 8 символов')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ password: newPassword })
      })

      if (response.ok) {
        alert('Пароль успешно изменен')
        setShowPasswordModal(false)
        setNewPassword('')
        setConfirmPassword('')
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка изменения пароля')
      }
    } catch (error) {
      alert('Ошибка изменения пароля')
    }
  }

  const handleDelete = async () => {
    if (!confirm('Вы уверены, что хотите удалить этого пользователя? Это действие необратимо.')) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        router.push('/managers')
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка удаления')
      }
    } catch (error) {
      alert('Ошибка удаления пользователя')
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked :
              type === 'number' ? parseInt(value) || 0 : value
    }))
  }

  // Копирование SMTP логина в IMAP
  const copySmtpToImap = () => {
    setFormData(prev => ({
      ...prev,
      imap_user: prev.smtp_user,
      imap_password: prev.smtp_password
    }))
  }

  if (loading) return (
    <LayoutWithSidebar>
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <div className="text-gray-500">Загрузка...</div>
        </div>
      </div>
    </LayoutWithSidebar>
  )

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button onClick={() => router.push('/managers')} className="p-2 hover:bg-gray-100 rounded-lg">
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <h1 className="text-xl font-semibold">Редактировать менеджера</h1>
              </div>
              <button onClick={handleDelete} className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center space-x-2">
                <Trash2 className="w-4 h-4" />
                <span>Удалить</span>
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 py-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Основная информация */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Основная информация</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Полное имя</label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Роль <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    required
                  >
                    <option value="manager">Менеджер</option>
                    <option value="admin">Администратор</option>
                    <option value="viewer">Наблюдатель</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-500">Дата создания</label>
                  <input
                    type="text"
                    value={formData.created_at ? new Date(formData.created_at).toLocaleString('ru') : ''}
                    className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-500"
                    disabled
                  />
                </div>

                <div className="flex items-center">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleChange}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm">Аккаунт активен</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Безопасность */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Безопасность</h2>
              <button
                type="button"
                onClick={() => setShowPasswordModal(true)}
                className="w-full px-4 py-3 border-2 border-dashed rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2 text-gray-600"
              >
                <Key className="w-5 h-5" />
                <span>Изменить пароль</span>
              </button>
            </div>

            {/* Выбор провайдера */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Почтовый провайдер</h2>
              <div>
                <label className="block text-sm font-medium mb-2">Выберите провайдера</label>
                <select
                  value={formData.email_provider_id}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">-- Не выбран --</option>
                  {providers.map(p => (
                    <option key={p.id} value={p.id}>{p.display_name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  При выборе провайдера настройки SMTP/IMAP заполнятся автоматически
                </p>
              </div>
            </div>

            {/* SMTP настройки */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Server className="w-5 h-5 text-blue-500" />
                <h2 className="text-lg font-semibold">Настройки SMTP (для отправки писем)</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
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
                  <label className="block text-sm font-medium mb-2">SMTP Порт</label>
                  <input
                    type="number"
                    name="smtp_port"
                    value={formData.smtp_port}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="587"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">SMTP Логин (Email)</label>
                  <input
                    type="text"
                    name="smtp_user"
                    value={formData.smtp_user}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="info@database-ai.ru"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">SMTP Пароль</label>
                  <div className="relative">
                    <input
                      type={showSmtpPassword ? 'text' : 'password'}
                      name="smtp_password"
                      value={formData.smtp_password}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10"
                      placeholder="Оставьте пустым, чтобы не менять"
                    />
                    <button
                      type="button"
                      onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showSmtpPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Имя отправителя</label>
                  <input
                    type="text"
                    name="smtp_from_name"
                    value={formData.smtp_from_name}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Database AI"
                  />
                </div>

                <div className="flex items-center">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="smtp_use_tls"
                      checked={formData.smtp_use_tls}
                      onChange={handleChange}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm">Использовать TLS/STARTTLS</span>
                  </label>
                </div>
              </div>
            </div>

            {/* IMAP настройки */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Inbox className="w-5 h-5 text-green-500" />
                  <h2 className="text-lg font-semibold">Настройки IMAP (для получения писем)</h2>
                </div>
                <button
                  type="button"
                  onClick={copySmtpToImap}
                  className="text-sm text-blue-500 hover:text-blue-700"
                >
                  Скопировать из SMTP
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
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
                  <label className="block text-sm font-medium mb-2">IMAP Порт</label>
                  <input
                    type="number"
                    name="imap_port"
                    value={formData.imap_port}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="993"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">IMAP Логин (Email)</label>
                  <input
                    type="text"
                    name="imap_user"
                    value={formData.imap_user}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="info@database-ai.ru"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">IMAP Пароль</label>
                  <div className="relative">
                    <input
                      type={showImapPassword ? 'text' : 'password'}
                      name="imap_password"
                      value={formData.imap_password}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10"
                      placeholder="Оставьте пустым, чтобы не менять"
                    />
                    <button
                      type="button"
                      onClick={() => setShowImapPassword(!showImapPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showImapPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center">
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
            </div>

            {/* Email шаблоны */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Mail className="w-5 h-5 text-purple-500" />
                <h2 className="text-lg font-semibold">Шаблоны писем по умолчанию</h2>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Тема письма</label>
                  <input
                    type="text"
                    name="email_default_subject"
                    value={formData.email_default_subject}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Тело письма</label>
                  <textarea
                    name="email_default_body"
                    value={formData.email_default_body}
                    onChange={handleChange}
                    rows={4}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Подпись</label>
                  <textarea
                    name="email_signature"
                    value={formData.email_signature}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Кнопки */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => router.push('/managers')}
                className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Сохранение...' : 'Сохранить изменения'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Модалка смены пароля */}
        {showPasswordModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Изменить пароль</h3>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Новый пароль <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10"
                      placeholder="Минимум 8 символов"
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Подтвердите пароль <span className="text-red-500">*</span>
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Повторите пароль"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  onClick={() => {
                    setShowPasswordModal(false)
                    setNewPassword('')
                    setConfirmPassword('')
                  }}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  onClick={handlePasswordChange}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Изменить пароль
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </LayoutWithSidebar>
  )
}
