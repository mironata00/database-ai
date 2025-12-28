import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Database AI - Suppliers Management',
  description: 'AI-powered supplier database management system',
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
