'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../layout-with-sidebar'
import { CheckCircle, XCircle, Clock, AlertCircle, FileText, Mail, Phone, MessageSquare, Calendar, User, MapPin, Briefcase, CreditCard, Download, RotateCcw } from 'lucide-react'

interface SupplierRequest {
  id: string
  status: 'pending' | 'approved' | 'rejected'
  data: {
    name: string
    inn: string
    legal_address: string
    actual_address: string
    contact_person: string
    contact_email: string
    contact_phone: string
    phone: string
    payment_terms: string
    delivery_regions: string[]
    color: string
  }
  contact_email: string | null
  contact_phone: string | null
  contact_telegram: string | null
  pricelist_filenames: string[] | null
  pricelist_urls: string[] | null
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
  rejection_reason: string | null
  notes: string | null
}

export default function RequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<SupplierRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('pending')
  const [selectedRequest, setSelectedRequest] = useState<SupplierRequest | null>(null)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [pendingCount, setPendingCount] = useState(0)
  const [useCategoryColors, setUseCategoryColors] = useState(true)
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => { checkAuth() }, [])
  useEffect(() => { fetchRequests() }, [filter])

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    if (!token) { router.push('/login'); return }
    const user = userData ? JSON.parse(userData) : null
    if (user?.role !== 'admin') { alert('Доступ запрещен'); router.push('/'); return }
    fetchCategorySettings()
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

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const url = filter === 'all' 
        ? `${API_URL}/api/supplier-requests/` 
        : `${API_URL}/api/supplier-requests/?status=${filter}`
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) throw new Error('Failed to fetch')
      
      const data = await response.json()
      setRequests(data.requests || [])
      
      if (filter === 'pending') {
        setPendingCount(data.total || 0)
      } else {
        const pendingRes = await fetch(`${API_URL}/api/supplier-requests/?status=pending`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (pendingRes.ok) {
          const pendingData = await pendingRes.json()
          setPendingCount(pendingData.total || 0)
        }
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const approve = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const userData = localStorage.getItem('user')
      const user = userData ? JSON.parse(userData) : null
      
      const formData = new FormData()
      formData.append('admin_email', user?.email || 'admin@system.local')
      
      const response = await fetch(`${API_URL}/api/supplier-requests/${id}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })
      
      if (response.ok) {
        alert('Заявка одобрена и поставщик создан')
        await fetchRequests()
        setSelectedRequest(null)
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка одобрения')
      }
    } catch (error) {
      console.error('Approve error:', error)
      alert('Ошибка одобрения заявки')
    }
  }

  const reject = async (id: string) => {
    if (!rejectReason.trim()) {
      alert('Укажите причину отклонения')
      return
    }
    
    try {
      const token = localStorage.getItem('access_token')
      const userData = localStorage.getItem('user')
      const user = userData ? JSON.parse(userData) : null
      
      const formData = new FormData()
      formData.append('admin_email', user?.email || 'admin@system.local')
      formData.append('reason', rejectReason)
      
      const response = await fetch(`${API_URL}/api/supplier-requests/${id}/reject`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })
      
      if (response.ok) {
        alert('Заявка отклонена')
        await fetchRequests()
        setShowRejectModal(false)
        setRejectReason('')
        setSelectedRequest(null)
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка отклонения')
      }
    } catch (error) {
      console.error('Reject error:', error)
      alert('Ошибка отклонения заявки')
    }
  }

  const reopen = async (id: string) => {
    if (!confirm('Вернуть заявку на рассмотрение?')) return
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/supplier-requests/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: 'pending' })
      })
      
      if (response.ok) {
        alert('Заявка возвращена на рассмотрение')
        await fetchRequests()
        setSelectedRequest(null)
      } else {
        const data = await response.json()
        alert(data.detail || 'Ошибка')
      }
    } catch (error) {
      console.error('Reopen error:', error)
      alert('Ошибка возврата заявки')
    }
  }

  const downloadPricelist = async (requestId: string, fileIndex: number, filename: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/supplier-requests/${requestId}/download/${fileIndex}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Ошибка скачивания файла')
      }
    } catch (error) {
      console.error('Download error:', error)
      alert('Ошибка скачивания файла')
    }
  }

  const getStatusBadge = (status: string) => {
    const config = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock, label: 'На проверке' },
      approved: { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle, label: 'Одобрено' },
      rejected: { bg: 'bg-red-100', text: 'text-red-700', icon: XCircle, label: 'Отклонено' }
    }
    const s = config[status as keyof typeof config] || config.pending
    const Icon = s.icon
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
        <Icon className="w-3.5 h-3.5 mr-1" />
        {s.label}
      </span>
    )
  }

  return (
    <LayoutWithSidebar pendingRequestsCount={pendingCount}>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <h1 className="text-xl font-semibold">Заявки на добавление поставщиков</h1>
          </div>
        </div>

        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex space-x-2">
              {[
                { key: 'all', label: 'Все' },
                { key: 'pending', label: 'На проверке' },
                { key: 'approved', label: 'Одобренные' },
                { key: 'rejected', label: 'Отклоненные' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === tab.key
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                <div className="text-gray-500">Загрузка...</div>
              </div>
            </div>
          ) : requests.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Заявок не найдено</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              {requests.map((req) => (
                <div key={req.id} className="bg-white rounded-lg border hover:shadow-md transition-shadow">
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold" style={useCategoryColors ? { backgroundColor: req.data.color } : { backgroundColor: '#6B7280' }}>
                          {req.data.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">{req.data.name}</h3>
                          <p className="text-xs text-gray-500">ИНН: {req.data.inn}</p>
                        </div>
                      </div>
                      {getStatusBadge(req.status)}
                    </div>

                    <div className="space-y-1.5 text-sm mb-3">
                      <div className="flex items-center text-gray-600">
                        <User className="w-4 h-4 mr-2 flex-shrink-0" />
                        <span className="truncate">{req.data.contact_person}</span>
                      </div>
                      <div className="flex items-center text-gray-600">
                        <Mail className="w-4 h-4 mr-2 flex-shrink-0" />
                        <span className="truncate">{req.data.contact_email}</span>
                      </div>
                      <div className="flex items-center text-gray-600">
                        <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
                        <span>{new Date(req.created_at).toLocaleString('ru')}</span>
                      </div>
                      {req.pricelist_filenames && req.pricelist_filenames.length > 0 && (
                        <div className="pt-1">
                          <div className="text-xs text-gray-500 mb-1">Прайс-листы ({req.pricelist_filenames.length}):</div>
                          {req.pricelist_filenames.map((filename, idx) => (
                            <button
                              key={idx}
                              onClick={() => downloadPricelist(req.id, idx, filename)}
                              className="flex items-center text-blue-600 hover:text-blue-800 text-xs mb-1 w-full"
                            >
                              <FileText className="w-3 h-3 mr-1 flex-shrink-0" />
                              <span className="truncate">{filename}</span>
                              <Download className="w-3 h-3 ml-1 flex-shrink-0" />
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {req.status === 'pending' && (
                      <div className="flex space-x-2 mb-2">
                        <button
                          onClick={() => approve(req.id)}
                          className="flex-1 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm font-medium"
                        >
                          Одобрить
                        </button>
                        <button
                          onClick={() => { setSelectedRequest(req); setShowRejectModal(true) }}
                          className="flex-1 px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium"
                        >
                          Отклонить
                        </button>
                      </div>
                    )}

                    {req.status === 'rejected' && (
                      <button
                        onClick={() => reopen(req.id)}
                        className="w-full mb-2 px-3 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm font-medium flex items-center justify-center"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Вернуть на рассмотрение
                      </button>
                    )}

                    <button
                      onClick={() => setSelectedRequest(req)}
                      className="w-full px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700"
                    >
                      Подробнее
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedRequest && !showRejectModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold">Детали заявки</h2>
                <button onClick={() => setSelectedRequest(null)} className="text-gray-400 hover:text-gray-600">
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
              
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="font-semibold mb-3">Основная информация</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-gray-500">Название:</span> <span className="font-medium">{selectedRequest.data.name}</span></div>
                    <div><span className="text-gray-500">ИНН:</span> <span className="font-medium">{selectedRequest.data.inn}</span></div>
                    <div><span className="text-gray-500">Юр. адрес:</span> <span>{selectedRequest.data.legal_address}</span></div>
                    <div><span className="text-gray-500">Факт. адрес:</span> <span>{selectedRequest.data.actual_address}</span></div>
                    <div><span className="text-gray-500">Условия оплаты:</span> <span>{selectedRequest.data.payment_terms}</span></div>
                    <div><span className="text-gray-500">Регионы:</span> <span>{selectedRequest.data.delivery_regions.join(', ')}</span></div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">Контактная информация</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="text-gray-500">Контактное лицо:</span> <span>{selectedRequest.data.contact_person}</span></div>
                    <div><span className="text-gray-500">Email:</span> <span>{selectedRequest.data.contact_email}</span></div>
                    <div><span className="text-gray-500">Телефон:</span> <span>{selectedRequest.data.contact_phone}</span></div>
                    <div><span className="text-gray-500">Телефон компании:</span> <span>{selectedRequest.data.phone}</span></div>
                  </div>
                </div>

                {selectedRequest.pricelist_filenames && selectedRequest.pricelist_filenames.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">Прайс-листы ({selectedRequest.pricelist_filenames.length})</h3>
                    <div className="space-y-2">
                      {selectedRequest.pricelist_filenames.map((filename, idx) => (
                        <button
                          key={idx}
                          onClick={() => downloadPricelist(selectedRequest.id, idx, filename)}
                          className="flex items-center space-x-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 w-full"
                        >
                          <FileText className="w-5 h-5" />
                          <span className="flex-1 text-left truncate">{filename}</span>
                          <Download className="w-4 h-4" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {selectedRequest.rejection_reason && (
                  <div>
                    <h3 className="font-semibold mb-3 text-red-600">Причина отклонения</h3>
                    <p className="text-sm bg-red-50 p-3 rounded-lg">{selectedRequest.rejection_reason}</p>
                  </div>
                )}

                {selectedRequest.status === 'pending' && (
                  <div className="flex space-x-4 pt-4 border-t">
                    <button onClick={() => approve(selectedRequest.id)} className="flex-1 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium">
                      Одобрить и добавить поставщика
                    </button>
                    <button onClick={() => setShowRejectModal(true)} className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium">
                      Отклонить заявку
                    </button>
                  </div>
                )}

                {selectedRequest.status === 'rejected' && (
                  <div className="flex space-x-4 pt-4 border-t">
                    <button onClick={() => reopen(selectedRequest.id)} className="flex-1 px-4 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 font-medium flex items-center justify-center">
                      <RotateCcw className="w-5 h-5 mr-2" />
                      Вернуть на рассмотрение
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {showRejectModal && selectedRequest && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-lg font-semibold mb-4">Причина отклонения</h3>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                rows={4}
                placeholder="Укажите причину отклонения заявки..."
              />
              <div className="flex space-x-3 mt-4">
                <button onClick={() => { setShowRejectModal(false); setRejectReason('') }} className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50">
                  Отмена
                </button>
                <button onClick={() => reject(selectedRequest.id)} className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600">
                  Отклонить
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </LayoutWithSidebar>
  )
}