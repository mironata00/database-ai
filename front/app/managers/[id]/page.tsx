'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { ArrowLeft, Save, Key, Eye, EyeOff, Trash2 } from 'lucide-react'

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
  const [formData, setFormData] = useState({ email: '', full_name: '', role: 'manager', is_active: true, created_at: '' })
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { fetchManager() }, [])

  const fetchManager = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, { headers: { 'Authorization': `Bearer ${token}` } })
      if (response.status === 401) { localStorage.clear(); router.push('/login'); return }
      if (response.ok) {
        const data = await response.json()
        setFormData({ email: data.email, full_name: data.full_name || '', role: data.role, is_active: data.is_active, created_at: data.created_at })
      } else { setError('Пользователь не найден') }
    } catch (error) { setError('Ошибка загрузки данных') } finally { setLoading(false) }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const token = localStorage.getItem('access_token')
      const payload = { email: formData.email, full_name: formData.full_name || null, role: formData.role, is_active: formData.is_active }
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify(payload)
      })
      if (response.status === 401) { localStorage.clear(); router.push('/login'); return }
      if (!response.ok) { const data = await response.json(); throw new Error(data.detail || 'Ошибка обновления') }
      router.push('/managers')
    } catch (err: any) { setError(err.message || 'Ошибка обновления') } finally { setSaving(false) }
  }

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) { alert('Пароли не совпадают'); return }
    if (newPassword.length < 8) { alert('Пароль должен содержать минимум 8 символов'); return }
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}/password`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ new_password: newPassword })
      })
      if (response.ok) { alert('Пароль успешно изменен'); setShowPasswordModal(false); setNewPassword(''); setConfirmPassword('') }
      else { const data = await response.json(); alert(data.detail || 'Ошибка изменения пароля') }
    } catch (error) { alert('Ошибка изменения пароля') }
  }

  const handleDelete = async () => {
    if (!confirm('Вы уверены, что хотите удалить этого пользователя? Это действие необратимо.')) return
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/managers/${params.id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } })
      if (response.ok) { router.push('/managers') } else { const data = await response.json(); alert(data.detail || 'Ошибка удаления') }
    } catch (error) { alert('Ошибка удаления пользователя') }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value }))
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
                <button onClick={() => router.push('/managers')} className="p-2 hover:bg-gray-100 rounded-lg"><ArrowLeft className="w-5 h-5" /></button>
                <h1 className="text-xl font-semibold">Редактировать пользователя</h1>
              </div>
              <button onClick={handleDelete} className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center space-x-2">
                <Trash2 className="w-4 h-4" /><span>Удалить</span>
              </button>
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
                  <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Полное имя</label>
                  <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Роль <span className="text-red-500">*</span></label>
                  <select name="role" value={formData.role} onChange={handleChange} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" required>
                    <option value="manager">Менеджер</option>
                    <option value="admin">Администратор</option>
                    <option value="viewer">Наблюдатель</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-500">Дата создания</label>
                  <input type="text" value={formData.created_at ? new Date(formData.created_at).toLocaleString('ru') : ''} className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-500" disabled />
                </div>
              </div>
            </div>
            <div className="mb-8">
              <h2 className="text-lg font-semibold mb-4">Безопасность</h2>
              <button type="button" onClick={() => setShowPasswordModal(true)} className="w-full px-4 py-3 border-2 border-dashed rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2 text-gray-600">
                <Key className="w-5 h-5" /><span>Изменить пароль</span>
              </button>
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
              <button type="submit" disabled={saving} className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2">
                <Save className="w-4 h-4" />
                <span>{saving ? 'Сохранение...' : 'Сохранить изменения'}</span>
              </button>
            </div>
          </form>
        </div>
        {showPasswordModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Изменить пароль</h3>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Новый пароль <span className="text-red-500">*</span></label>
                  <div className="relative">
                    <input type={showPassword ? 'text' : 'password'} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none pr-10" placeholder="Минимум 8 символов" minLength={8} />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Подтвердите пароль <span className="text-red-500">*</span></label>
                  <input type={showPassword ? 'text' : 'password'} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Повторите пароль" />
                </div>
              </div>
              <div className="flex justify-end space-x-4">
                <button onClick={() => { setShowPasswordModal(false); setNewPassword(''); setConfirmPassword('') }} className="px-4 py-2 border rounded-lg hover:bg-gray-50">Отмена</button>
                <button onClick={handlePasswordChange} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">Изменить пароль</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </LayoutWithSidebar>
  )
}
