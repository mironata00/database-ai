'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, CheckCircle, XCircle, Download, Mail, Phone, MessageSquare } from 'lucide-react'

export default function RequestDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [request, setRequest] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)

  const API_URL = typeof window !== 'undefined'
    ? `https://${window.location.hostname}`
    : 'http://localhost'

  useEffect(() => {
    fetchRequest()
  }, [])

  const fetchRequest = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/supplier-requests/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setRequest(data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!confirm('Одобрить заявку и создать поставщика?')) return

    setProcessing(true)
    try {
      const token = localStorage.getItem('access_token')
      const adminEmail = localStorage.getItem('user_email') || 'admin@database-ai.ru'
      
      const formData = new FormData()
      formData.append('admin_email', adminEmail)

      const response = await fetch(`${API_URL}/api/supplier-requests/${params.id}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (response.ok) {
        alert('Заявка одобрена! Поставщик создан.')
        router.push('/requests')
      } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail}`)
      }
    } catch (error) {
      alert('Ошибка одобрения')
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      alert('Укажите причину отклонения')
      return
    }

    setProcessing(true)
    try {
      const token = localStorage.getItem('access_token')
      const adminEmail = localStorage.getItem('user_email') || 'admin@database-ai.ru'
      
      const formData = new FormData()
      formData.append('admin_email', adminEmail)
      formData.append('reason', rejectionReason)

      const response = await fetch(`${API_URL}/api/supplier-requests/${params.id}/reject`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (response.ok) {
        alert('Заявка отклонена')
        router.push('/requests')
      } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail}`)
      }
    } catch (error) {
      alert('Ошибка отклонения')
    } finally {
      setProcessing(false)
      setShowRejectModal(false)
    }
  }

  const downloadPricelist = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/supplier-requests/${params.id}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = request.pricelist_filename
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      alert('Ошибка загрузки файла')
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div>Загрузка...</div></div>
  if (!request) return <div className="min-h-screen flex items-center justify-center"><div>Заявка не найдена</div></div>

  const InfoRow = ({ label, value }: { label: string; value: any }) => {
    if (!value) return null
    return (
      <div className="flex justify-between py-2 border-b">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{value}</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <button onClick={() => router.push('/requests')} className="p-2 hover:bg-gray-100 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold">Заявка: {request.data.name}</h1>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Данные компании</h2>
              <div className="space-y-1">
                <InfoRow label="Название" value={request.data.name} />
                <InfoRow label="ИНН" value={request.data.inn} />
                <InfoRow label="КПП" value={request.data.kpp} />
                <InfoRow label="ОГРН" value={request.data.ogrn} />
                <InfoRow label="Юридический адрес" value={request.data.legal_address} />
                <InfoRow label="Фактический адрес" value={request.data.actual_address} />
                <InfoRow label="Email" value={request.data.email} />
                <InfoRow label="Телефон" value={request.data.phone} />
                <InfoRow label="Сайт" value={request.data.website} />
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Контактное лицо</h2>
              <div className="space-y-1">
                <InfoRow label="ФИО" value={request.data.contact_person} />
                <InfoRow label="Должность" value={request.data.contact_position} />
                <InfoRow label="Телефон" value={request.data.contact_phone} />
                <InfoRow label="Email" value={request.data.contact_email} />
              </div>
            </div>

            {request.notes && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Примечания</h2>
                <p className="whitespace-pre-wrap">{request.notes}</p>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Статус</h2>
              <div className="mb-4">
                {request.status === 'pending' && <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full">На рассмотрении</span>}
                {request.status === 'approved' && <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full">Одобрено</span>}
                {request.status === 'rejected' && <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full">Отклонено</span>}
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>Подано: {new Date(request.created_at).toLocaleString('ru')}</div>
                {request.reviewed_at && <div>Рассмотрено: {new Date(request.reviewed_at).toLocaleString('ru')}</div>}
                {request.reviewed_by && <div>Кем: {request.reviewed_by}</div>}
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Контакты для связи</h2>
              <div className="space-y-3">
                {request.contact_email && <div className="flex items-center space-x-2 text-sm">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <span>{request.contact_email}</span>
                </div>}
                {request.contact_phone && <div className="flex items-center space-x-2 text-sm">
                  <Phone className="w-4 h-4 text-gray-400" />
                  <span>{request.contact_phone}</span>
                </div>}
                {request.contact_telegram && <div className="flex items-center space-x-2 text-sm">
                  <MessageSquare className="w-4 h-4 text-gray-400" />
                  <span>{request.contact_telegram}</span>
                </div>}
              </div>
            </div>

            {request.pricelist_filename && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Прайс-лист</h2>
                <div className="text-sm mb-3">{request.pricelist_filename}</div>
                <button onClick={downloadPricelist} className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg flex items-center justify-center space-x-2">
                  <Download className="w-4 h-4" />
                  <span>Скачать</span>
                </button>
              </div>
            )}

            {request.status === 'pending' && (
              <div className="bg-white rounded-lg border p-6 space-y-3">
                <button
                  onClick={handleApprove}
                  disabled={processing}
                  className="w-full px-4 py-2 bg-green-500 text-white rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Одобрить</span>
                </button>
                <button
                  onClick={() => setShowRejectModal(true)}
                  disabled={processing}
                  className="w-full px-4 py-2 bg-red-500 text-white rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Отклонить</span>
                </button>
              </div>
            )}

            {request.status === 'rejected' && request.rejection_reason && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="font-semibold text-red-800 mb-2">Причина отклонения</h3>
                <p className="text-sm text-red-700">{request.rejection_reason}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Причина отклонения</h3>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Укажите причину отклонения заявки..."
              className="w-full px-3 py-2 border rounded-lg mb-4"
              rows={4}
            />
            <div className="flex space-x-3">
              <button
                onClick={handleReject}
                disabled={processing}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg disabled:opacity-50"
              >
                Отклонить
              </button>
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 rounded-lg"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
