'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { Save, Upload } from 'lucide-react'

const AVAILABLE_COLORS = [
  { hex: '#3B82F6', name: 'Синий (Вода)', category: 'water' },
  { hex: '#EAB308', name: 'Желтый (Электрика)', category: 'electric' },
  { hex: '#92400E', name: 'Коричневый (Дерево)', category: 'wood' },
  { hex: '#9333EA', name: 'Фиолетовый (Химия)', category: 'chemical' },
  { hex: '#6B7280', name: 'Серый (Разное)', category: 'other' },
  { hex: '#EF4444', name: 'Красный', category: 'custom' },
  { hex: '#10B981', name: 'Зеленый', category: 'custom' },
  { hex: '#F59E0B', name: 'Оранжевый', category: 'custom' },
]

export default function AddSupplierPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [selectedColor, setSelectedColor] = useState('#3B82F6')

  const [formData, setFormData] = useState({
    name: '',
    inn: '',
    kpp: '',
    ogrn: '',
    email: '',
    phone: '',
    website: '',
    legal_address: '',
    actual_address: '',
    contact_person: '',
    contact_position: '',
    contact_phone: '',
    contact_email: '',
    delivery_regions: '',
    payment_terms: '',
    min_order_sum: '',
    notes: '',
  })

  const API_URL = typeof window !== 'undefined' 
    ? `http://${window.location.hostname}`
    : 'http://localhost'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        router.push('/login')
        return
      }

      const payload: any = {
        name: formData.name,
        inn: formData.inn,
        color: selectedColor,
      }
      
      if (formData.kpp) payload.kpp = formData.kpp
      if (formData.ogrn) payload.ogrn = formData.ogrn
      if (formData.email) payload.email = formData.email
      if (formData.phone) payload.phone = formData.phone
      if (formData.website) payload.website = formData.website
      if (formData.legal_address) payload.legal_address = formData.legal_address
      if (formData.actual_address) payload.actual_address = formData.actual_address
      if (formData.contact_person) payload.contact_person = formData.contact_person
      if (formData.contact_position) payload.contact_position = formData.contact_position
      if (formData.contact_phone) payload.contact_phone = formData.contact_phone
      if (formData.contact_email) payload.contact_email = formData.contact_email
      if (formData.payment_terms) payload.payment_terms = formData.payment_terms
      if (formData.min_order_sum) payload.min_order_sum = parseFloat(formData.min_order_sum)
      if (formData.notes) payload.notes = formData.notes
      if (formData.delivery_regions) {
        payload.delivery_regions = formData.delivery_regions.split(',').map(r => r.trim())
      }

      const response = await fetch(`${API_URL}/api/suppliers/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })

      if (response.status === 401) {
        localStorage.clear()
        router.push('/login')
        return
      }

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Ошибка создания поставщика')
      }

      const supplier = await response.json()

      // Загрузить файл если выбран
      if (file) {
        const formData = new FormData()
        formData.append('file', file)

        const uploadResponse = await fetch(`${API_URL}/api/suppliers/${supplier.id}/upload-pricelist-new`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        })

        if (!uploadResponse.ok) {
          console.error('Ошибка загрузки файла')
        }
      }

      router.push('/')
    } catch (err: any) {
      setError(err.message || 'Ошибка создания поставщика')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  return (
    <LayoutWithSidebar>
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold">Добавить поставщика</h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="bg-white rounded-lg border p-6">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Выбор цвета */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Цветовая категория</h2>
            <p className="text-sm text-gray-600 mb-4">
              Выберите цвет для визуальной категоризации поставщика. 
              После загрузки прайс-листа цвет может быть автоматически определен по категориям товаров.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {AVAILABLE_COLORS.map((color) => (
                <button
                  key={color.hex}
                  type="button"
                  onClick={() => setSelectedColor(color.hex)}
                  className={`flex items-center space-x-3 p-3 border-2 rounded-lg hover:shadow-md transition ${
                    selectedColor === color.hex ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div 
                    className="w-8 h-8 rounded-full border-2 border-gray-300" 
                    style={{ backgroundColor: color.hex }}
                  />
                  <span className="text-sm font-medium">{color.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Основная информация */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Основная информация</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-2">
                  Название компании <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  ИНН <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="inn"
                  value={formData.inn}
                  onChange={handleChange}
                  pattern="[0-9]{10,12}"
                  maxLength={12}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">КПП</label>
                <input
                  type="text"
                  name="kpp"
                  value={formData.kpp}
                  onChange={handleChange}
                  pattern="[0-9]{9}"
                  maxLength={9}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">ОГРН</label>
                <input
                  type="text"
                  name="ogrn"
                  value={formData.ogrn}
                  onChange={handleChange}
                  pattern="[0-9]{13,15}"
                  maxLength={15}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Телефон</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Сайт</label>
                <input
                  type="text"
                  name="website"
                  value={formData.website}
                  onChange={handleChange}
                  placeholder="example.com"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Адреса */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Адреса</h2>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Юридический адрес</label>
                <input
                  type="text"
                  name="legal_address"
                  value={formData.legal_address}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Фактический адрес</label>
                <input
                  type="text"
                  name="actual_address"
                  value={formData.actual_address}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Регионы доставки (через запятую)</label>
                <input
                  type="text"
                  name="delivery_regions"
                  value={formData.delivery_regions}
                  onChange={handleChange}
                  placeholder="Москва, Московская область"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Контактное лицо */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Контактное лицо</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">ФИО</label>
                <input
                  type="text"
                  name="contact_person"
                  value={formData.contact_person}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Должность</label>
                <input
                  type="text"
                  name="contact_position"
                  value={formData.contact_position}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Телефон контакта</label>
                <input
                  type="tel"
                  name="contact_phone"
                  value={formData.contact_phone}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Email контакта</label>
                <input
                  type="email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Условия работы */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Условия работы</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Условия оплаты</label>
                <input
                  type="text"
                  name="payment_terms"
                  value={formData.payment_terms}
                  onChange={handleChange}
                  placeholder="Постоплата 14 дней"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Минимальная сумма заказа (₽)</label>
                <input
                  type="number"
                  name="min_order_sum"
                  value={formData.min_order_sum}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Прайс-лист */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Прайс-лист (опционально)</h2>
            <div className="border-2 border-dashed rounded-lg p-6">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                accept=".xlsx,.xls,.csv,.pdf"
                className="hidden"
              />
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center cursor-pointer"
              >
                <Upload className="w-12 h-12 text-gray-400 mb-2" />
                <span className="text-sm text-gray-600">
                  {file ? file.name : 'Нажмите для выбора файла или перетащите сюда'}
                </span>
                <span className="text-xs text-gray-400 mt-1">
                  Поддерживаются: Excel, CSV, PDF
                </span>
              </label>
            </div>
          </div>

          {/* Примечания */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Примечания</h2>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Дополнительная информация"
            />
          </div>

          {/* Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => router.push('/')}
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
              <span>{loading ? 'Сохранение...' : 'Сохранить'}</span>
            </button>
          </div>
        </form>
      </div>
    </LayoutWithSidebar>
  )
}
