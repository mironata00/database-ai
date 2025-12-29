import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Database AI - CRM поставщиков строительных материалов',
  description: 'AI-powered supplier database management system',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}
