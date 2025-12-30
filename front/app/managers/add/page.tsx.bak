'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save, Eye, EyeOff } from 'lucide-react'

export default function AddManagerPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({ email: '', password: '', confirmPassword: '', full_name: '', role: 'manager', is_active: true })
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (formData.password !== formData.confirmPassword) { setError('Пароли не совпадают'); return }
    if (formData.password.length < 8) { setError('Пароль должен содержать минимум 8 символов'); return }
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) { router.push('/login'); return }
      const payload = { email: formData.email, password: formData.password, full_name: formData.full_name || null, role: formData.role, is_active: formData.is_active }
      const response = await fetch(`${API_URL}/api/managers/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(payload)
      })
      if (response.status === 401) { localStorage.clear(); router.push('/login'); return }
      if (!response.ok) { const data = await response.json(); throw new Error(data.detail || 'Ошибка создания') }
      router.push('/managers')
    } catch (err: any) {
      setError(err.message || 'Ошибка создания пользователя')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value }))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <button onClick={() => router.push('/managers')} className="p-2 hover:bg-gray-100 rounded-lg"><ArrowLeft className="w-5 h-5" /></button>
            <h1 className="text-xl font-semibold">Добавить пользователя</h1>
          </div>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="bg-white rounded-lg border p-6">
          {error && <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Основная информация</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Email <span className="text-red-500">*</span></label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="user@company.ru" required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Полное имя</label>
                <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Иван Иванов" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Роль <span className="text-red-500">*</span></label>
                <select name="role" value={formData.role} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" required>
                  <option value="manager">Менеджер</option>
                  <option value="admin">Администратор</option>
                  <option value="viewer">Наблюдатель</option>
                </select>
              </div>
            </div>
          </div>
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Пароль</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Пароль <span className="text-red-500">*</span></label>
                <div className="relative">
                  <input type={showPassword ? 'text' : 'password'} name="password" value={formData.password} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10" placeholder="Минимум 8 символов" required minLength={8} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Подтвердите пароль <span className="text-red-500">*</span></label>
                <input type={showPassword ? 'text' : 'password'} name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Повторите пароль" required />
              </div>
            </div>
          </div>
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Статус</h2>
            <label className="flex items-center space-x-3">
              <input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
              <span className="text-sm">Аккаунт активен</span>
            </label>
          </div>
          <div className="flex justify-end space-x-4">
            <button type="button" onClick={() => router.push('/managers')} className="px-6 py-2 border rounded-lg hover:bg-gray-50">Отмена</button>
            <button type="submit" disabled={loading} className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2">
              <Save className="w-4 h-4" />
              <span>{loading ? 'Сохранение...' : 'Создать пользователя'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
