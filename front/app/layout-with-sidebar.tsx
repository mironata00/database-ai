'use client'

import { useRouter, usePathname } from 'next/navigation'
import { Home, Building2, FileText, LogOut, UserCog } from 'lucide-react'
import { useEffect, useState } from 'react'

interface User {
  id: string
  email: string
  full_name: string
  role: string
}

export default function LayoutWithSidebar({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) setUser(JSON.parse(userData))
  }, [])

  const handleLogout = () => {
    localStorage.clear()
    router.push('/login')
  }

  const menuItems = [
    { icon: Home, label: 'База поставщиков', path: '/' },
    { icon: FileText, label: 'Заявки на проверку', path: '/requests', badge: 1 },
  ]

  if (user?.role === 'admin') {
    menuItems.splice(1, 0, { icon: UserCog, label: 'Менеджеры', path: '/managers', badge: undefined })
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-lg">DB</div>
            <div><h1 className="font-semibold">DataBase AI</h1></div>
          </div>
        </div>

        {user && (
          <div className="px-6 py-4 border-b border-slate-700">
            <div className="text-xs text-slate-400 mb-2">ПОЛЬЗОВАТЕЛЬ</div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-semibold">
                {user.full_name?.charAt(0) || 'A'}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{user.full_name}</div>
                <div className="text-xs text-slate-400 capitalize">{user.role}</div>
              </div>
            </div>
          </div>
        )}

        <nav className="flex-1 p-4 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600 text-white font-medium' : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">{item.badge}</span>
                )}
              </button>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-slate-800 text-slate-300"
          >
            <LogOut className="w-5 h-5" />
            <span>Выйти</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
