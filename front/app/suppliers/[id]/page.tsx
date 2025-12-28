'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, Mail, Phone, Globe, MapPin, Star, Upload, FileText, X, Plus } from 'lucide-react'

export default function SupplierDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [supplier, setSupplier] = useState<any>(null)
  const [imports, setImports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newRating, setNewRating] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

  const API_URL = typeof window !== 'undefined' 
    ? `http://${window.location.hostname}`
    : 'http://localhost'

  useEffect(() => {
    fetchSupplier()
    fetchImports()
    const interval = setInterval(fetchImports, 5000)
    return () => clearInterval(interval)
  }, [])

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

  const saveTags = async (newTags: string[]) => {
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

  const handleRatingUpdate = async () => {
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
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const newTags = [...tags, newTag.trim()]
      setTags(newTags)
      setNewTag('')
      saveTags(newTags)
    }
  }

  const removeTag = (tagToRemove: string) => {
    const newTags = tags.filter(t => t !== tagToRemove)
    setTags(newTags)
    saveTags(newTags)
  }

  const handleFileUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const token = localStorage.getItem('access_token')
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/api/suppliers/${params.id}/upload-pricelist-new`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (response.ok) {
        setFile(null)
        fetchImports()
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><div>Загрузка...</div></div>
  }

  if (!supplier) {
    return <div className="min-h-screen flex items-center justify-center"><div>Не найден</div></div>
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

  const latestImport = imports[0]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button onClick={() => router.push('/')} className="p-2 hover:bg-gray-100 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold">{supplier.name}</h1>
          </div>
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

            {supplier.notes && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold mb-4">Примечания</h2>
                <p className="whitespace-pre-wrap">{supplier.notes}</p>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Рейтинг</h2>
              <div className="flex items-center space-x-3 mb-4">
                <Star className="w-12 h-12 text-yellow-500 fill-yellow-500" />
                <span className="text-4xl font-bold">{supplier.rating?.toFixed(1) || '0.0'}</span>
              </div>
              <div className="flex space-x-2">
                <input
                  type="number"
                  step="0.1"
                  value={newRating}
                  onChange={(e) => setNewRating(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleRatingUpdate()}
                  className="flex-1 px-3 py-2 border rounded-lg"
                />
                <button onClick={handleRatingUpdate} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                  OK
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Теги</h2>
              <div className="mb-3 flex space-x-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag()}
                  placeholder="Добавить тег..."
                  className="flex-1 px-3 py-2 border rounded-lg text-sm"
                />
                <button onClick={addTag} className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {tags.map((tag, i) => (
                  <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm flex items-center space-x-1 group">
                    <span>{tag}</span>
                    <button onClick={() => removeTag(tag)} className="hover:text-red-600 opacity-0 group-hover:opacity-100 transition">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold mb-4">Прайс-лист</h2>
              
              {latestImport && (
                <div className="mb-4 p-3 bg-gray-50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium truncate">{latestImport.file_name}</span>
                    {latestImport.status === 'processing' && <span className="text-xs text-yellow-600">⏳</span>}
                    {latestImport.status === 'completed' && <span className="text-xs text-green-600">✓</span>}
                  </div>
                  
                  {latestImport.status === 'processing' && latestImport.total_products > 0 && (
                    <div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${Math.min(100, (latestImport.parsed_products / latestImport.total_products) * 100)}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-600">
                        {latestImport.parsed_products} / {latestImport.total_products} ({Math.round((latestImport.parsed_products / latestImport.total_products) * 100)}%)
                      </div>
                    </div>
                  )}
                  
                  {latestImport.file_url && (
                    <a href={latestImport.file_url} download className="text-xs text-blue-600 hover:underline flex items-center space-x-1 mt-2">
                      <FileText className="w-3 h-3" />
                      <span>Скачать файл</span>
                    </a>
                  )}
                </div>
              )}
              
              <input
                type="file"
                id="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                accept=".xlsx,.xls,.csv"
                className="hidden"
              />
              <label htmlFor="file" className="cursor-pointer block border-2 border-dashed rounded p-4 text-center hover:bg-gray-50">
                <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <div className="text-sm text-gray-600">{file ? file.name : 'Загрузить новый'}</div>
              </label>
              {file && (
                <button onClick={handleFileUpload} disabled={uploading} className="mt-3 w-full px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50">
                  {uploading ? 'Загрузка...' : 'Загрузить'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
