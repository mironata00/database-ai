'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { CheckCircle, XCircle, Clock, Eye } from 'lucide-react'

export default function RequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  const API_URL = typeof window !== 'undefined'
    ? `http://${window.location.hostname}`
    : 'http://localhost'

  useEffect(() => {
    fetchRequests()
  }, [filter])

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const url = filter === 'all' 
        ? `${API_URL}/api/requests/`
        : `${API_URL}/api/requests/?status=${filter}`
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRequests(data.requests || [])
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs inline-flex items-center space-x-1">
          <Clock className="w-3 h-3" />
          <span>На рассмотрении</span>
        </span>
      case 'approved':
        return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs inline-flex items-center space-x-1">
          <CheckCircle className="w-3 h-3" />
          <span>Одобрено</span>
        </span>
      case 'rejected':
        return <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs inline-flex items-center space-x-1">
          <XCircle className="w-3 h-3" />
          <span>Отклонено</span>
        </span>
      default:
        return null
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div>Загрузка...</div></div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold">Заявки на проверку</h1>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6 flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg ${filter === 'all' ? 'bg-blue-500 text-white' : 'bg-white border'}`}
          >
            Все
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg ${filter === 'pending' ? 'bg-blue-500 text-white' : 'bg-white border'}`}
          >
            На рассмотрении
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`px-4 py-2 rounded-lg ${filter === 'approved' ? 'bg-blue-500 text-white' : 'bg-white border'}`}
          >
            Одобрено
          </button>
          <button
            onClick={() => setFilter('rejected')}
            className={`px-4 py-2 rounded-lg ${filter === 'rejected' ? 'bg-blue-500 text-white' : 'bg-white border'}`}
          >
            Отклонено
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {requests.map((request) => (
            <div key={request.id} className="bg-white rounded-lg border p-4 hover:shadow-lg transition-shadow cursor-pointer"
                 onClick={() => router.push(`/requests/${request.id}`)}>
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-lg">{request.data.name || 'Без названия'}</h3>
                {getStatusBadge(request.status)}
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div><strong>ИНН:</strong> {request.data.inn || '—'}</div>
                <div><strong>Email:</strong> {request.contact_email || '—'}</div>
                <div><strong>Телефон:</strong> {request.contact_phone || '—'}</div>
                <div><strong>Дата подачи:</strong> {new Date(request.created_at).toLocaleDateString('ru')}</div>
              </div>

              <div className="mt-4 pt-4 border-t flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {request.pricelist_filename ? '📎 Прайс-лист прикреплён' : 'Без прайс-листа'}
                </span>
                <button className="text-blue-600 hover:underline text-sm inline-flex items-center space-x-1">
                  <Eye className="w-4 h-4" />
                  <span>Открыть</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {requests.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Нет заявок
          </div>
        )}
      </div>
    </div>
  )
}
