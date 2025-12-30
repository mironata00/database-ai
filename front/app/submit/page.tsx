'use client'

import { useState } from 'react'
import { Upload, Send, CheckCircle } from 'lucide-react'

export default function SubmitRequestPage() {
  const [formData, setFormData] = useState({
    name: '',
    inn: '',
    kpp: '',
    ogrn: '',
    legal_address: '',
    actual_address: '',
    email: '',
    phone: '',
    website: '',
    contact_person: '',
    contact_position: '',
    contact_phone: '',
    contact_email: '',
    payment_terms: '',
    min_order_sum: '',
    delivery_regions: '',
    notes: ''
  })

  const [contactData, setContactData] = useState({
    contact_email: '',
    contact_phone: '',
    contact_telegram: ''
  })

  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  const API_URL = typeof window !== 'undefined'
    ? `https://${window.location.hostname}`
    : 'http://localhost'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name || !formData.inn) {
      alert('Заполните обязательные поля: Название и ИНН')
      return
    }

    setSubmitting(true)

    try {
      const requestFormData = new FormData()
      
      // Преобразуем delivery_regions в массив
      const supplierData = {
        ...formData,
        delivery_regions: formData.delivery_regions 
          ? formData.delivery_regions.split(',').map(r => r.trim())
          : [],
        min_order_sum: formData.min_order_sum ? parseFloat(formData.min_order_sum) : null
      }

      requestFormData.append('data', JSON.stringify(supplierData))
      requestFormData.append('contact_email', contactData.contact_email)
      requestFormData.append('contact_phone', contactData.contact_phone)
      requestFormData.append('contact_telegram', contactData.contact_telegram)
      requestFormData.append('notes', formData.notes)
      
      if (file) {
        requestFormData.append('pricelist', file)
      }

      const response = await fetch(`${API_URL}/api/requests/`, {
        method: 'POST',
        body: requestFormData
      })

      if (response.ok) {
        setSuccess(true)
        // Очищаем форму
        setFormData({
          name: '', inn: '', kpp: '', ogrn: '', legal_address: '', actual_address: '',
          email: '', phone: '', website: '', contact_person: '', contact_position: '',
          contact_phone: '', contact_email: '', payment_terms: '', min_order_sum: '',
          delivery_regions: '', notes: ''
        })
        setContactData({ contact_email: '', contact_phone: '', contact_telegram: '' })
        setFile(null)
      } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail}`)
      }
    } catch (error) {
      alert('Ошибка отправки заявки')
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg border p-8 max-w-md w-full text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Заявка отправлена!</h2>
          <p className="text-gray-600 mb-6">
            Мы получили вашу заявку и рассмотрим её в ближайшее время. 
            Вы получите уведомление на указанный email.
          </p>
          <button
            onClick={() => setSuccess(false)}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg"
          >
            Отправить ещё
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold">Заявка на добавление в базу поставщиков</h1>
          <p className="text-gray-600 mt-2">
            Заполните форму, и мы рассмотрим вашу заявку в течение 1-2 рабочих дней
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Основные данные */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Данные компании *</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Название организации *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="ООО 'Название'"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">ИНН *</label>
                <input
                  type="text"
                  required
                  value={formData.inn}
                  onChange={(e) => setFormData({...formData, inn: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="1234567890"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">КПП</label>
                <input
                  type="text"
                  value={formData.kpp}
                  onChange={(e) => setFormData({...formData, kpp: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">ОГРН</label>
                <input
                  type="text"
                  value={formData.ogrn}
                  onChange={(e) => setFormData({...formData, ogrn: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Юридический адрес</label>
                <input
                  type="text"
                  value={formData.legal_address}
                  onChange={(e) => setFormData({...formData, legal_address: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Фактический адрес</label>
                <input
                  type="text"
                  value={formData.actual_address}
                  onChange={(e) => setFormData({...formData, actual_address: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* Контакты компании */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Контакты</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Телефон</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Сайт</label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({...formData, website: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="https://"
                />
              </div>
            </div>
          </div>

          {/* Контактное лицо */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Контактное лицо</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">ФИО</label>
                <input
                  type="text"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Должность</label>
                <input
                  type="text"
                  value={formData.contact_position}
                  onChange={(e) => setFormData({...formData, contact_position: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Телефон</label>
                <input
                  type="tel"
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* Условия работы */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Условия работы</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Условия оплаты</label>
                <input
                  type="text"
                  value={formData.payment_terms}
                  onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="Предоплата, отсрочка..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Минимальная сумма заказа</label>
                <input
                  type="number"
                  value={formData.min_order_sum}
                  onChange={(e) => setFormData({...formData, min_order_sum: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="₽"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Регионы доставки (через запятую)</label>
                <input
                  type="text"
                  value={formData.delivery_regions}
                  onChange={(e) => setFormData({...formData, delivery_regions: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="Москва, Московская область, Санкт-Петербург"
                />
              </div>
            </div>
          </div>

          {/* Прайс-лист */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Прайс-лист</h2>
            <input
              type="file"
              id="pricelist"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              accept=".xlsx,.xls,.csv"
              className="hidden"
            />
            <label htmlFor="pricelist" className="cursor-pointer block border-2 border-dashed rounded-lg p-6 text-center hover:bg-gray-50">
              <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <div className="text-sm text-gray-600">
                {file ? file.name : 'Загрузите прайс-лист (необязательно)'}
              </div>
              <div className="text-xs text-gray-400 mt-1">Форматы: XLSX, XLS, CSV</div>
            </label>
          </div>

          {/* Контакты для связи */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Ваши контакты для уведомлений</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Email *</label>
                <input
                  type="email"
                  required
                  value={contactData.contact_email}
                  onChange={(e) => setContactData({...contactData, contact_email: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="your@email.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Телефон</label>
                <input
                  type="tel"
                  value={contactData.contact_phone}
                  onChange={(e) => setContactData({...contactData, contact_phone: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="+7 (999) 123-45-67"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Telegram (username)</label>
                <input
                  type="text"
                  value={contactData.contact_telegram}
                  onChange={(e) => setContactData({...contactData, contact_telegram: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="@username"
                />
              </div>
            </div>
          </div>

          {/* Примечания */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Дополнительная информация</h2>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              rows={4}
              placeholder="Укажите дополнительную информацию о вашей компании..."
            />
          </div>

          {/* Кнопка отправки */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="px-8 py-3 bg-blue-500 text-white rounded-lg flex items-center space-x-2 disabled:opacity-50 hover:bg-blue-600 transition-colors"
            >
              <Send className="w-5 h-5" />
              <span>{submitting ? 'Отправка...' : 'Отправить заявку'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
