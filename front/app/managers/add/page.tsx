'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { ArrowLeft, Save, Eye, EyeOff, Mail, Server } from 'lucide-react'

export default function AddManagerPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showSmtpPassword, setShowSmtpPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    role: 'manager',
    is_active: true,
    smtp_host: 'smtp.jino.ru',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_from_name: '',
    email_default_subject: 'Запрос цен',
    email_default_body: 'Добрый день!\n\nПросим предоставить актуальные цены и сроки поставки на следующие товары:',
    email_signature: 'С уважением,\nОтдел закупок'
  })
  
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (formData.password !== formData.confirmPassword) {
      setError('Пароли не совпадают')
      return
    }
    
    if (formData.password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов')
      return
    }
    
    setLoading(true)
    
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }
      
      const payload = {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || null,
        role: formData.role,
        is_active: formData.is_active,
        smtp_host: formData.smtp_host || null,
        smtp_port: formData.smtp_port || 587,
        smtp_user: formData.smtp_user || null,
        smtp_password: formData.smtp_password || null,
        smtp_use_tls: formData.smtp_use_tls,
        smtp_from_name: formData.smtp_from_name || null,
        email_default_subject: formData.email_default_subject,
        email_default_body: formData.email_default_body,
        email_signature: formData.email_signature
      }
      
      const response = await fetch(`${API_URL}/api/managers/`, {
        method: 'POST',
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
        throw new Error(data.detail || 'Ошибка создания')
      }
      
      router.push('/managers')
    } catch (err: any) {
      setError(err.message || 'Ошибка создания пользователя')
    } finally {
      setLoading(false)
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

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center space-x-4">
              <button onClick={() => router.push('/managers')} className="p-2 hover:bg-gray-100 rounded-lg">
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-xl font-semibold">Добавить менеджера</h1>
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
                    placeholder="manager@company.ru"
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
                    placeholder="Иван Иванов"
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
            
            {/* Пароль */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Пароль для входа</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Пароль <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10"
                      placeholder="Минимум 8 символов"
                      required
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
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Повторите пароль"
                    required
                  />
                </div>
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
                      placeholder="Пароль от почты"
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
            
            {/* Email шаблоны */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Mail className="w-5 h-5 text-green-500" />
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
                    placeholder="Запрос цен"
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
                disabled={loading}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>{loading ? 'Создание...' : 'Создать менеджера'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </LayoutWithSidebar>
  )
}
