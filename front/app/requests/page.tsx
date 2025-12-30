'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../layout-with-sidebar'
import { CheckCircle, XCircle, Clock } from 'lucide-react'

export default function RequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [userRole, setUserRole] = useState<string>('')

  const API_URL = typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.host}`
    : 'http://localhost'

  const isAdmin = userRole === 'admin'

  useEffect(() => {
    const user = localStorage.getItem('user')
    if (user) {
      try {
        const userData = JSON.parse(user)
        setUserRole(userData.role || '')
      } catch (e) {
        console.error('Error parsing user data:', e)
      }
    }
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

  const approveRequest = async (requestId: string) => {
    if (!isAdmin) return
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/requests/${requestId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        fetchRequests()
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const rejectRequest = async (requestId: string) => {
    if (!isAdmin) return
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/requests/${requestId}/reject`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        fetchRequests()
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium inline-flex items-center space-x-1">
          <Clock className="w-4 h-4" />
          <span>На проверке</span>
        </span>
      case 'approved':
        return <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium inline-flex items-center space-x-1">
          <CheckCircle className="w-4 h-4" />
          <span>Одобрена</span>
        </span>
      case 'rejected':
        return <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium inline-flex items-center space-x-1">
          <XCircle className="w-4 h-4" />
          <span>Отклонена</span>
        </span>
      default:
        return null
    }
  }

  if (loading) {
    return (
      <LayoutWithSidebar>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div>
            <div className="text-gray-500">Загрузка...</div>
          </div>
        </div>
      </LayoutWithSidebar>
    )
  }

  return (
    <LayoutWithSidebar>
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold">Заявки на добавление поставщиков</h1>
          {!isAdmin && (
            <p className="text-sm text-gray-500 mt-1">Режим просмотра (менеджер)</p>
          )}
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
            className={`px-4 py-2 rounded-lg ${filter === 'pending' ? 'bg-yellow-500 text-white' : 'bg-white border'}`}
          >
            На проверке
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`px-4 py-2 rounded-lg ${filter === 'approved' ? 'bg-green-500 text-white' : 'bg-white border'}`}
          >
            Одобрены
          </button>
          <button
            onClick={() => setFilter('rejected')}
            className={`px-4 py-2 rounded-lg ${filter === 'rejected' ? 'bg-red-500 text-white' : 'bg-white border'}`}
          >
            Отклонены
          </button>
        </div>

        <div className="space-y-4">
          {requests.map((request) => (
            <div 
              key={request.id} 
              className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden"
              style={{ borderLeft: `3px solid ${request.status === 'pending' ? '#EAB308' : request.status === 'approved' ? '#10B981' : '#EF4444'}` }}
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-3">
                      <h3 className="text-xl font-semibold">{request.company_name || request.data?.name || 'Без названия'}</h3>
                      {getStatusBadge(request.status)}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-gray-500">ИНН:</p>
                        <p className="font-medium">{request.inn || request.data?.inn || '—'}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Email:</p>
                        <p className="font-medium">{request.email || request.contact_email || '—'}</p>
                      </div>
                    </div>

                    {(request.comment || request.data?.comment) && (
                      <div className="mb-4">
                        <p className="text-sm text-gray-500">Комментарий:</p>
                        <p className="text-gray-700">{request.comment || request.data?.comment}</p>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2">
                      {(request.phone || request.contact_phone) && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                          {request.phone || request.contact_phone}
                        </span>
                      )}
                      {(request.website || request.data?.website) && (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                          {request.website || request.data?.website}
                        </span>
                      )}
                      {request.pricelist_filename && (
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded">
                          📎 {request.pricelist_filename}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 ml-6">
                    <span className="text-yellow-500 text-2xl">★</span>
                    <span className="text-lg font-medium text-gray-700">0.0</span>
                  </div>
                </div>

                {isAdmin && request.status === 'pending' && (
                  <div className="flex items-center justify-between mt-6 pt-6 border-t">
                    <button
                      onClick={() => rejectRequest(request.id)}
                      className="px-6 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                    >
                      В черный список
                    </button>
                    <button
                      onClick={() => approveRequest(request.id)}
                      className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                    >
                      Подтвердить и добавить
                    </button>
                  </div>
                )}
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
    </LayoutWithSidebar>
  )
}
