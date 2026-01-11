'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { Save, Upload, X } from 'lucide-react'

const STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Активен' },
  { value: 'INACTIVE', label: 'Неактивен' },
  { value: 'BLACKLIST', label: 'Черный список' },
]

export default function AddSupplierPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedStatus, setSelectedStatus] = useState('ACTIVE')
  const [categories, setCategories] = useState<any>({})
  const [useCategoryColors, setUseCategoryColors] = useState(true)

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
    postal_address: '',
    edo: '',
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
    ? `${window.location.protocol}//${window.location.host}`
    : 'http://localhost'

  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/suppliers/categories`)
      if (response.ok) {
        const data = await response.json()
        setCategories(data.categories || {})
        setUseCategoryColors(data.use_category_colors || false)
      }
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

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
        status: selectedStatus,
        categories: selectedCategories,
      }
      
      if (formData.kpp) payload.kpp = formData.kpp
      if (formData.ogrn) payload.ogrn = formData.ogrn
      if (formData.email) payload.email = formData.email
      if (formData.phone) payload.phone = formData.phone
      if (formData.website) payload.website = formData.website
      if (formData.legal_address) payload.legal_address = formData.legal_address
      if (formData.actual_address) payload.actual_address = formData.actual_address
      if (formData.postal_address) payload.postal_address = formData.postal_address
      if (formData.edo) payload.edo = formData.edo
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

      // Загрузка всех прайс-листов
      if (files.length > 0) {
        for (const file of files) {
          const formData = new FormData()
          formData.append('file', file)

          await fetch(`${API_URL}/api/suppliers/${supplier.id}/upload-pricelist-new`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
          })
        }
      }

      router.push('/suppliers')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(prev => [...prev, ...Array.from(e.target.files!)])
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const toggleCategory = (categoryKey: string) => {
    setSelectedCategories(prev => 
      prev.includes(categoryKey)
        ? prev.filter(c => c !== categoryKey)
        : [...prev, categoryKey]
    )
  }

  return (
    <LayoutWithSidebar>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <h1 className="text-xl font-semibold">Добавить поставщика</h1>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 py-8">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-white rounded-lg border p-6 space-y-6">
            {/* Статус */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Статус <span className="text-red-500">*</span>
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              >
                {STATUS_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Направления работы */}
            <div>
              <label className="block text-sm font-medium mb-3">
                Направления работы
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(categories).map(([key, value]: [string, any]) => {
                  const isSelected = selectedCategories.includes(key)
                  return (
                    <div
                      key={key}
                      onClick={() => toggleCategory(key)}
                      className={`p-3 rounded-lg border-2 cursor-pointer transition ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      style={useCategoryColors && isSelected 
                        ? { borderLeftWidth: '4px', borderLeftColor: value.color }
                        : {}
                      }
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{value.name}</span>
                        {isSelected && (
                          <span className="text-blue-500">✓</span>
                        )}
                      </div>
                      {useCategoryColors && (
                        <div 
                          className="w-full h-1 rounded mt-2"
                          style={{ backgroundColor: value.color }}
                        />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Основная информация */}
            <div>
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

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-2">Сайт</label>
                  <input
                    type="url"
                    name="website"
                    value={formData.website}
                    onChange={handleChange}
                    placeholder="https://example.com"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Контактное лицо */}
            <div>
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
                  <label className="block text-sm font-medium mb-2">Телефон</label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
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

            {/* Адреса */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Адреса</h2>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Юридический адрес</label>
                  <textarea
                    name="legal_address"
                    value={formData.legal_address}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Фактический адрес</label>
                  <textarea
                    name="actual_address"
                    value={formData.actual_address}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Почтовый адрес</label>
                  <textarea
                    name="postal_address"
                    value={formData.postal_address}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">ЭДО</label>
                  <input
                    type="text"
                    name="edo"
                    value={formData.edo}
                    onChange={handleChange}
                    placeholder="Диадок, СБИС, Контур и т.д."
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Условия работы */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Условия работы</h2>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Регионы доставки</label>
                  <input
                    type="text"
                    name="delivery_regions"
                    value={formData.delivery_regions}
                    onChange={handleChange}
                    placeholder="Москва, Московская область, Санкт-Петербург"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <p className="text-xs text-gray-500 mt-1">Через запятую</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Условия оплаты</label>
                  <textarea
                    name="payment_terms"
                    value={formData.payment_terms}
                    onChange={handleChange}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Минимальная сумма заказа</label>
                  <input
                    type="number"
                    name="min_order_sum"
                    value={formData.min_order_sum}
                    onChange={handleChange}
                    step="0.01"
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Примечания</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleChange}
                    rows={3}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Загрузка прайс-листов */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Прайс-листы (можно несколько)
              </label>
              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".xlsx,.xls,.csv"
                  multiple
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer"
                >
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-sm text-gray-600 mb-1">
                    <span className="text-blue-600 font-medium">Нажмите для выбора файлов</span> или перетащите их сюда
                  </p>
                  <p className="text-xs text-gray-500">
                    Excel, CSV, PDF • Максимум 100 МБ на файл
                  </p>
                </label>
              </div>
              
              {files.length > 0 && (
                <div className="mt-3 space-y-2">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <Upload className="w-5 h-5 text-blue-500 flex-shrink-0" />
                        <span className="text-sm truncate">{file.name}</span>
                        <span className="text-xs text-gray-500 flex-shrink-0">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Кнопки */}
            <div className="flex items-center gap-3 pt-4 border-t">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Сохранение...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Создать поставщика
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => router.back()}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      </div>
    </LayoutWithSidebar>
  )
}
