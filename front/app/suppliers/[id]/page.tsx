'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { Mail, Phone, Globe, MapPin, Star, Upload, Download, X, Plus, Trash2, Palette, Edit2, Check, ChevronDown, ChevronUp } from 'lucide-react'

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

const STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Активен', color: 'green' },
  { value: 'INACTIVE', label: 'Неактивен', color: 'gray' },
  { value: 'BLACKLIST', label: 'Черный список', color: 'red' },
]

const TAGS_PER_PAGE = 50

export default function SupplierDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [supplier, setSupplier] = useState<any>(null)
  const [imports, setImports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState<any>('')
  const [editingStatus, setEditingStatus] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [tags, setTags] = useState<string[]>([])
  const [displayedTagsCount, setDisplayedTagsCount] = useState(TAGS_PER_PAGE)
  const [tagsExpanded, setTagsExpanded] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [userRole, setUserRole] = useState<string>('')
  const [newRating, setNewRating] = useState('')
  const prevImportsRef = useRef<any[]>([])

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

    fetchSupplier()
    fetchImports()
    const interval = setInterval(fetchImports, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const prevImports = prevImportsRef.current
    const hadProcessing = prevImports.some(imp => imp.status === 'processing')
    const hasNewCompleted = imports.some(imp => {
      const wasProcessing = prevImports.find(prev => prev.id === imp.id && prev.status === 'processing')
      return imp.status === 'completed' && wasProcessing
    })

    if (hadProcessing && hasNewCompleted) {
      fetchSupplier()
    }

    prevImportsRef.current = imports
  }, [imports])

  const fetchSupplier = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setSupplier(data)
        setNewRating(data.rating?.toString() || '0')
        setTags(data.tags_array || [])
        setSelectedStatus(data.status || 'ACTIVE')
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchImports = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}/imports`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setImports(data.imports || [])
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const startEdit = (field: string, currentValue: any) => {
    if (!isAdmin) return
    setEditingField(field)
    setEditValue(currentValue || '')
  }

  const saveField = async (field: string) => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ [field]: editValue })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setEditingField(null)
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Ошибка сохранения')
    }
  }

  const saveStatus = async () => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: selectedStatus })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setEditingStatus(false)
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Ошибка сохранения статуса')
    }
  }

  const handleRatingUpdate = async () => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ rating: parseFloat(newRating) })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const updateColor = async (newColor: string) => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ color: newColor })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setShowColorPicker(false)
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const updateTags = async (newTags: string[]) => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ tags_array: newTags })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setTags(newTags)
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const addTag = () => {
    if (!isAdmin || newTag.trim() === '' || tags.includes(newTag.trim())) return
    const newTags = [...tags, newTag.trim()]
    setTags(newTags)
    updateTags(newTags)
    setNewTag('')
  }

  const removeTag = (tagToRemove: string) => {
    if (!isAdmin) return
    const newTags = tags.filter(t => t !== tagToRemove)
    setTags(newTags)
    updateTags(newTags)
  }

  const clearAllTags = () => {
    if (!isAdmin || !confirm('Удалить все теги?')) return
    setTags([])
    updateTags([])
  }

  const loadMoreTags = () => {
    setDisplayedTagsCount(prev => Math.min(prev + TAGS_PER_PAGE, tags.length))
  }

  const toggleTagsExpanded = () => {
    if (tagsExpanded) {
      setDisplayedTagsCount(TAGS_PER_PAGE)
      setTagsExpanded(false)
    } else {
      setDisplayedTagsCount(tags.length)
      setTagsExpanded(true)
    }
  }

  const handleFileUpload = async () => {
    if (!file || !isAdmin) return
    setUploading(true)
    setUploadProgress(0)

    try {
      const token = localStorage.getItem('access_token')
      const formData = new FormData()
      formData.append('file', file)

      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100)
          setUploadProgress(percent)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          setFile(null)
          setUploadProgress(0)
          fetchImports()
        }
        setUploading(false)
      })

      xhr.addEventListener('error', () => {
        setUploading(false)
        setUploadProgress(0)
        alert('Ошибка загрузки')
      })

      xhr.open('POST', `${API_URL}/api/suppliers/${params.id}/upload-pricelist-new`)
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(formData)
    } catch (error) {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const deleteImport = async (importId: string) => {
    if (!isAdmin || !confirm('Удалить этот прайс-лист?')) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}/imports/${importId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        fetchImports()
      }
    } catch (error) {
      alert('Ошибка удаления')
    }
  }

  const downloadFile = async (importId: string, fileName: string) => {
    const token = localStorage.getItem('access_token')
    const url = `${API_URL}/api/suppliers/${params.id}/imports/${importId}/download`

    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.ok) {
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = fileName
      a.click()
      window.URL.revokeObjectURL(downloadUrl)
    }
  }

  const EditableField = ({ label, value, field, type = 'text', placeholder = '' }: any) => {
    const isEditing = editingField === field

    return (
      <div className="flex justify-between items-center py-3 border-b hover:bg-gray-50 group">
        <span className="text-gray-600 font-medium">{label}</span>
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <>
              <input
                type={type}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="px-3 py-1 border rounded focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder={placeholder}
                autoFocus
              />
              <button onClick={() => saveField(field)} className="p-1 text-green-600 hover:bg-green-50 rounded">
                <Check className="w-4 h-4" />
              </button>
              <button onClick={() => setEditingField(null)} className="p-1 text-gray-600 hover:bg-gray-100 rounded">
                <X className="w-4 h-4" />
              </button>
            </>
          ) : (
            <>
              <span className={`${value ? 'font-medium' : 'text-gray-400 italic'}`}>
                {value || placeholder || 'Не указано'}
              </span>
              {isAdmin && (
                <button
                  onClick={() => startEdit(field, value)}
                  className="p-1 text-blue-600 opacity-0 group-hover:opacity-100 hover:bg-blue-50 rounded"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
            </>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <LayoutWithSidebar>
        <div className="flex items-center justify-center h-screen">
          <div className="text-gray-500">Загрузка...</div>
        </div>
      </LayoutWithSidebar>
    )
  }

  if (!supplier) {
    return (
      <LayoutWithSidebar>
        <div className="flex items-center justify-center h-screen">
          <div className="text-gray-500">Поставщик не найден</div>
        </div>
      </LayoutWithSidebar>
    )
  }

  const displayedTags = tags.slice(0, displayedTagsCount)
  const hasMoreTags = displayedTagsCount < tags.length

  return (
    <LayoutWithSidebar>
      <div className="bg-white border-b" style={{ borderLeft: `3px solid ${supplier.color}` }}>
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold">{supplier.name}</h1>
          {!isAdmin && <p className="text-sm text-gray-500 mt-1">Режим просмотра (менеджер)</p>}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Реквизиты */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Реквизиты</h2>
              <div className="space-y-1">
                <EditableField label="Название компании" value={supplier.name} field="name" placeholder="Введите название" />
                <EditableField label="ИНН" value={supplier.inn} field="inn" placeholder="Введите ИНН" />
                <EditableField label="КПП" value={supplier.kpp} field="kpp" placeholder="Введите КПП" />
                <EditableField label="ОГРН" value={supplier.ogrn} field="ogrn" placeholder="Введите ОГРН" />
              </div>
            </div>

            {/* Контакты */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Контакты</h2>
              <div className="space-y-1">
                <EditableField label="Email" value={supplier.email} field="email" type="email" placeholder="Введите email" />
                <EditableField label="Телефон" value={supplier.phone} field="phone" type="tel" placeholder="Введите телефон" />
                <EditableField label="Сайт" value={supplier.website} field="website" placeholder="Введите сайт" />
              </div>
            </div>

            {/* Контактное лицо */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Контактное лицо</h2>
              <div className="space-y-1">
                <EditableField label="ФИО" value={supplier.contact_person} field="contact_person" placeholder="Введите ФИО" />
                <EditableField label="Должность" value={supplier.contact_position} field="contact_position" placeholder="Введите должность" />
                <EditableField label="Телефон" value={supplier.contact_phone} field="contact_phone" type="tel" placeholder="Введите телефон" />
                <EditableField label="Email" value={supplier.contact_email} field="contact_email" type="email" placeholder="Введите email" />
              </div>
            </div>

            {/* Адреса */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Адреса</h2>
              <div className="space-y-1">
                <EditableField label="Юридический адрес" value={supplier.legal_address} field="legal_address" placeholder="Введите адрес" />
                <EditableField label="Фактический адрес" value={supplier.actual_address} field="actual_address" placeholder="Введите адрес" />
              </div>
            </div>

            {/* Условия работы */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Условия работы</h2>
              <div className="space-y-1">
                <EditableField label="Условия оплаты" value={supplier.payment_terms} field="payment_terms" placeholder="Введите условия" />
                <EditableField label="Мин. сумма заказа (₽)" value={supplier.min_order_sum} field="min_order_sum" type="number" placeholder="0" />
              </div>
            </div>

            {/* Примечания */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Примечания</h2>
              <EditableField label="" value={supplier.notes} field="notes" placeholder="Добавьте примечания" />
            </div>
          </div>

          <div className="space-y-6">
            {/* Статус */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Статус</h2>
              <div className="flex justify-between items-center py-2 hover:bg-gray-50 group">
                <div className="flex items-center space-x-2">
                  {editingStatus ? (
                    <>
                      <select
                        value={selectedStatus}
                        onChange={(e) => setSelectedStatus(e.target.value)}
                        className="px-3 py-1 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        autoFocus
                      >
                        {STATUS_OPTIONS.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                      <button onClick={saveStatus} className="p-1 text-green-600 hover:bg-green-50 rounded">
                        <Check className="w-4 h-4" />
                      </button>
                      <button onClick={() => { setEditingStatus(false); setSelectedStatus(supplier.status); }} className="p-1 text-gray-600 hover:bg-gray-100 rounded">
                        <X className="w-4 h-4" />
                      </button>
                    </>
                  ) : (
                    <>
                      <span className={`px-3 py-1 text-sm rounded-full ${
                        supplier.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                        supplier.status === 'BLACKLIST' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {STATUS_OPTIONS.find(s => s.value === supplier.status)?.label || supplier.status}
                      </span>
                      {isAdmin && (
                        <button
                          onClick={() => { setEditingStatus(true); setSelectedStatus(supplier.status); }}
                          className="p-1 text-blue-600 opacity-0 group-hover:opacity-100 hover:bg-blue-50 rounded"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Цвет категории */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Цвет категории</h2>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 rounded-full border-2 border-gray-300" style={{ backgroundColor: supplier.color }} />
                  <span className="text-sm text-gray-600">{AVAILABLE_COLORS.find(c => c.hex === supplier.color)?.name || 'Цвет'}</span>
                </div>
                {isAdmin && (
                  <button onClick={() => setShowColorPicker(!showColorPicker)} className="p-2 hover:bg-gray-100 rounded-lg">
                    <Palette className="w-5 h-5" />
                  </button>
                )}
              </div>

              {isAdmin && showColorPicker && (
                <div className="grid grid-cols-2 gap-2">
                  {AVAILABLE_COLORS.map((color) => (
                    <button
                      key={color.hex}
                      onClick={() => updateColor(color.hex)}
                      className={`flex items-center space-x-2 p-2 border rounded-lg hover:bg-gray-50 ${supplier.color === color.hex ? 'border-blue-500 bg-blue-50' : ''}`}
                    >
                      <div className="w-6 h-6 rounded-full border" style={{ backgroundColor: color.hex }} />
                      <span className="text-xs">{color.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Рейтинг */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Рейтинг</h2>
              <div className="flex items-center space-x-3 mb-4">
                <Star className="w-12 h-12 text-yellow-500 fill-yellow-500" />
                <span className="text-4xl font-bold">{supplier.rating?.toFixed(1) || '0.0'}</span>
              </div>
              {isAdmin && (
                <div className="flex space-x-2">
                  <input
                    type="number"
                    step="0.1"
                    value={newRating}
                    onChange={(e) => setNewRating(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-lg"
                  />
                  <button onClick={handleRatingUpdate} className="px-4 py-2 bg-blue-500 text-white rounded-lg">OK</button>
                </div>
              )}
            </div>

            {/* Теги - оптимизированное отображение */}
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Теги ({tags.length})</h2>
                {isAdmin && tags.length > 0 && (
                  <button onClick={clearAllTags} className="text-xs text-red-600 hover:underline flex items-center space-x-1">
                    <Trash2 className="w-3 h-3" />
                    <span>Очистить все</span>
                  </button>
                )}
              </div>
              
              {isAdmin && (
                <div className="mb-3 flex space-x-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addTag()}
                    placeholder="Добавить..."
                    className="flex-1 px-3 py-2 border rounded-lg text-sm"
                  />
                  <button onClick={addTag} className="px-3 py-2 bg-blue-500 text-white rounded-lg">
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              )}

              {tags.length > 0 ? (
                <>
                  <div className="flex flex-wrap gap-2 mb-3 max-h-[400px] overflow-y-auto">
                    {displayedTags.map((tag, i) => (
                      <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm flex items-center space-x-1 group">
                        <span>{tag}</span>
                        {isAdmin && (
                          <button onClick={() => removeTag(tag)} className="hover:text-red-600 opacity-0 group-hover:opacity-100">
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </span>
                    ))}
                  </div>

                  {tags.length > TAGS_PER_PAGE && (
                    <div className="flex flex-col space-y-2">
                      {hasMoreTags && !tagsExpanded && (
                        <button 
                          onClick={loadMoreTags}
                          className="w-full px-4 py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 flex items-center justify-center space-x-1"
                        >
                          <span>Показать ещё {Math.min(TAGS_PER_PAGE, tags.length - displayedTagsCount)}</span>
                          <ChevronDown className="w-4 h-4" />
                        </button>
                      )}
                      
                      <button 
                        onClick={toggleTagsExpanded}
                        className="w-full px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-1"
                      >
                        {tagsExpanded ? (
                          <>
                            <span>Свернуть</span>
                            <ChevronUp className="w-4 h-4" />
                          </>
                        ) : (
                          <>
                            <span>Показать все ({tags.length})</span>
                            <ChevronDown className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-sm text-gray-400 italic">Нет тегов</div>
              )}
            </div>

            {/* Прайс-листы */}
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Прайс-листы ({imports.length})</h2>

              {isAdmin && (
                <div className="mb-4">
                  <input type="file" id="file" onChange={(e) => setFile(e.target.files?.[0] || null)} accept=".xlsx,.xls,.csv" className="hidden" />
                  <label htmlFor="file" className="cursor-pointer block border-2 border-dashed rounded p-4 text-center hover:bg-gray-50">
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <div className="text-sm text-gray-600">{file ? file.name : 'Загрузить'}</div>
                  </label>
                  {file && (
                    <div className="mt-3">
                      {uploading && (
                        <div className="mb-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full transition-all" style={{width: `${uploadProgress}%`}} />
                          </div>
                          <div className="text-xs text-center mt-1 text-gray-600">{uploadProgress}%</div>
																											</div>
																											)}
																											<button onClick={handleFileUpload} disabled={uploading} className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50">
																											{uploading ? 'Загрузка...' : 'Загрузить'}
																											</button>
																											</div>
																											)}
																											</div>
																											)}
																											<div className="space-y-2">
            {imports.map((imp) => (
              <div key={imp.id} className="p-3 bg-gray-50 rounded border">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1 truncate">
                    <div className="text-sm font-medium truncate">{imp.file_name}</div>
                    <div className="text-xs text-gray-500">{new Date(imp.created_at).toLocaleString('ru')}</div>
                  </div>
                  <div>
                    {imp.status === 'processing' && <span className="text-xs text-yellow-600">⏳</span>}
                    {imp.status === 'completed' && <span className="text-xs text-green-600">✓</span>}
                    {imp.status === 'pending' && <span className="text-xs text-gray-600">⏸</span>}
                  </div>
                </div>

                {imp.status === 'processing' && imp.total_products > 0 && (
                  <div className="mb-2">
                    <div className="w-full bg-gray-200 rounded-full h-1 mb-1">
                      <div className="bg-green-500 h-1 rounded-full" style={{width: `${(imp.parsed_products / imp.total_products) * 100}%`}} />
                    </div>
                    <div className="text-xs text-gray-600">{imp.parsed_products} / {imp.total_products}</div>
                  </div>
                )}

                <div className="flex items-center space-x-3">
                  <button onClick={() => downloadFile(imp.id, imp.file_name)} className="text-xs text-blue-600 hover:underline flex items-center space-x-1">
                    <Download className="w-3 h-3" />
                    <span>Скачать</span>
                  </button>
                  {isAdmin && (
                    <button onClick={() => deleteImport(imp.id)} className="text-xs text-red-600 hover:underline flex items-center space-x-1">
                      <Trash2 className="w-3 h-3" />
                      <span>Удалить</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
</LayoutWithSidebar>
)
}
