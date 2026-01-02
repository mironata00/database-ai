'use client'

import { useRouter, usePathname } from 'next/navigation'
import { Home, Users, FileText, Settings, LogOut } from 'lucide-react'
import { useEffect, useState } from 'react'

interface LayoutProps {
  children: React.ReactNode
  pendingRequestsCount?: number
}

export default function LayoutWithSidebar({ children, pendingRequestsCount: externalCount }: LayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [pendingCount, setPendingCount] = useState(externalCount || 0)
  const [user, setUser] = useState<any>(null)
  const API_URL = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : 'http://localhost'

  useEffect(() => {
    // Загружаем данные пользователя из localStorage
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
  }, [])

  const fetchPendingCount = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return
      
      const response = await fetch(`${API_URL}/api/supplier-requests/?status=pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setPendingCount(data.total || 0)
      }
    } catch (error) {
      console.error('Error fetching pending count:', error)
    }
  }

  useEffect(() => {
    fetchPendingCount()
    const interval = setInterval(fetchPendingCount, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (externalCount !== undefined) {
      setPendingCount(externalCount)
    }
  }, [externalCount])

  const handleLogout = () => {
    localStorage.clear()
    router.push('/login')
  }

  const isAdmin = user?.role === 'admin'

  // Навигация с проверкой роли
  const allNavigation = [
    { name: 'Главная', href: '/', icon: Home, roles: ['admin', 'manager', 'viewer'] },
    { name: 'База поставщиков', href: '/suppliers', icon: Users, roles: ['admin', 'manager', 'viewer'] },
    { name: 'Менеджеры', href: '/managers', icon: Settings, roles: ['admin'] },
    { name: 'Заявки на проверку', href: '/requests', icon: FileText, badge: pendingCount, roles: ['admin'] }
  ]

  // Фильтруем навигацию по роли пользователя
  const navigation = allNavigation.filter(item => 
    item.roles.includes(user?.role || 'viewer')
  )

  const getRoleName = (role: string) => {
    const roleNames: Record<string, string> = {
      admin: 'Администратор',
      manager: 'Менеджер',
      viewer: 'Наблюдатель'
    }
    return roleNames[role] || role
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">
              DB
            </div>
            <span className="font-semibold text-lg">Database AI</span>
          </div>
        </div>

        {user && (
          <div className="p-4 border-b border-gray-800">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-semibold">
                {user.full_name?.charAt(0) || user.email?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.full_name || user.email}</p>
                <p className="text-xs text-gray-400">{getRoleName(user.role)}</p>
              </div>
            </div>
          </div>
        )}

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <button
                key={item.name}
                onClick={() => router.push(item.href)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg text-left transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className="font-medium text-sm truncate">{item.name}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full min-w-[24px] text-center flex-shrink-0 ml-2">
                    {item.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium text-sm">Выход</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  )
}
