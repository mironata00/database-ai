'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import LayoutWithSidebar from '../../layout-with-sidebar'
import { Mail, Phone, Globe, MapPin, Star, Upload, Download, X, Plus, Trash2, Palette } from 'lucide-react'

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

export default function SupplierDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [supplier, setSupplier] = useState<any>(null)
  const [imports, setImports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newRating, setNewRating] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [selectedColor, setSelectedColor] = useState('#3B82F6')
  const [userRole, setUserRole] = useState<string>('')
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
      console.log('Парсинг завершён! Обновляю теги...')
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
        setSelectedColor(data.color || '#3B82F6')
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

  const saveTags = async (newTags: string[]) => {
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
        setTags(updated.tags_array || [])
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const saveColor = async (color: string) => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ color })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setSelectedColor(updated.color)
        setShowColorPicker(false)
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const handleRatingUpdate = async () => {
    if (!isAdmin) return
    const rating = parseFloat(newRating)
    if (isNaN(rating)) return

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/suppliers/${params.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ rating })
      })

      if (response.ok) {
        const updated = await response.json()
        setSupplier(updated)
        setNewRating(updated.rating?.toString() || '0')
      }
    } catch (error) {
      console.error('Error:', error)
    }
  }

  const addTag = () => {
    if (!isAdmin || newTag.trim() === '' || tags.includes(newTag.trim())) return
    const newTags = [...tags, newTag.trim()]
    setTags(newTags)
    setNewTag('')
    saveTags(newTags)
  }

  const removeTag = (tagToRemove: string) => {
    if (!isAdmin) return
    const newTags = tags.filter(t => t !== tagToRemove)
    setTags(newTags)
    saveTags(newTags)
  }

  const clearAllTags = () => {
    if (!isAdmin || !confirm('Удалить все теги?')) return
    setTags([])
    saveTags([])
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
    <LayoutWithSidebar>
      <div 
        className="bg-white border-b"
        style={{ borderLeft: `3px solid ${selectedColor}` }}
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold">{supplier.name}</h1>
          {!isAdmin && (
            <p className="text-sm text-gray-500 mt-1">Режим просмотра (менеджер)</p>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Реквизиты</h2>
              <div className="space-y-1">
                <InfoRow label="ИНН" value={supplier.inn} />
                <InfoRow label="КПП" value={supplier.kpp} />
                <InfoRow label="ОГРН" value={supplier.ogrn} />
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Контакты</h2>
              <div className="space-y-3">
                {supplier.email && <div className="flex items-center space-x-2"><Mail className="w-4 h-4 text-gray-400" /><a href={`mailto:${supplier.email}`} className="text-blue-600">{supplier.email}</a></div>}
                {supplier.phone && <div className="flex items-center space-x-2"><Phone className="w-4 h-4 text-gray-400" /><span>{supplier.phone}</span></div>}
                {supplier.website && <div className="flex items-center space-x-2"><Globe className="w-4 h-4 text-gray-400" /><a href={supplier.website} target="_blank" className="text-blue-600">{supplier.website}</a></div>}
              </div>
            </div>

            {(supplier.contact_person || supplier.contact_phone || supplier.contact_email) && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Контактное лицо</h2>
                <div className="space-y-2">
                  <InfoRow label="ФИО" value={supplier.contact_person} />
                  <InfoRow label="Должность" value={supplier.contact_position} />
                  {supplier.contact_phone && <div className="flex items-center space-x-2 py-2"><Phone className="w-4 h-4 text-gray-400" /><span>{supplier.contact_phone}</span></div>}
                  {supplier.contact_email && <div className="flex items-center space-x-2 py-2"><Mail className="w-4 h-4 text-gray-400" /><a href={`mailto:${supplier.contact_email}`} className="text-blue-600">{supplier.contact_email}</a></div>}
                </div>
              </div>
            )}

            {(supplier.legal_address || supplier.actual_address) && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Адреса</h2>
                <div className="space-y-3">
                  {supplier.legal_address && <div><div className="text-sm text-gray-600 mb-1">Юридический</div><div className="flex items-start space-x-2"><MapPin className="w-4 h-4 text-gray-400 mt-1" /><span>{supplier.legal_address}</span></div></div>}
                  {supplier.actual_address && <div><div className="text-sm text-gray-600 mb-1">Фактический</div><div className="flex items-start space-x-2"><MapPin className="w-4 h-4 text-gray-400 mt-1" /><span>{supplier.actual_address}</span></div></div>}
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Условия работы</h2>
              <div className="space-y-1">
                <InfoRow label="Оплата" value={supplier.payment_terms} />
                <InfoRow label="Мин. сумма" value={supplier.min_order_sum ? `${supplier.min_order_sum} ₽` : null} />
                {supplier.delivery_regions && supplier.delivery_regions.length > 0 && (
                  <div className="py-2">
                    <div className="text-gray-600 mb-2">Регионы</div>
                    <div className="flex flex-wrap gap-2">
                      {supplier.delivery_regions.map((r: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-gray-100 rounded text-sm">{r}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {supplier.notes && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Примечания</h2>
                <p className="whitespace-pre-wrap">{supplier.notes}</p>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Цвет категории</h2>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-12 h-12 rounded-full border-2 border-gray-300" 
                    style={{ backgroundColor: selectedColor }}
                  />
                  <span className="text-sm text-gray-600">
                    {AVAILABLE_COLORS.find(c => c.hex === selectedColor)?.name || 'Цвет'}
                  </span>
                </div>
                {isAdmin && (
                  <button
                    onClick={() => setShowColorPicker(!showColorPicker)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    <Palette className="w-5 h-5" />
                  </button>
                )}
              </div>

              {isAdmin && showColorPicker && (
                <div className="grid grid-cols-2 gap-2">
                  {AVAILABLE_COLORS.map((color) => (
                    <button
                      key={color.hex}
                      onClick={() => saveColor(color.hex)}
                      className={`flex items-center space-x-2 p-2 border rounded-lg hover:bg-gray-50 ${
                        selectedColor === color.hex ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                    >
                      <div 
                        className="w-6 h-6 rounded-full border" 
                        style={{ backgroundColor: color.hex }}
                      />
                      <span className="text-xs">{color.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

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
                    onKeyDown={(e) => e.key === 'Enter' && handleRatingUpdate()}
                    className="flex-1 px-3 py-2 border rounded-lg"
                  />
                  <button onClick={handleRatingUpdate} className="px-4 py-2 bg-blue-500 text-white rounded-lg">
                    OK
                  </button>
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Теги</h2>
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
              <div className="flex flex-wrap gap-2">
                {tags.map((tag, i) => (
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
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Прайс-листы ({imports.length})</h2>

              {isAdmin && (
                <div className="mb-4">
                  <input
                    type="file"
                    id="file"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    accept=".xlsx,.xls,.csv"
                    className="hidden"
                  />
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
