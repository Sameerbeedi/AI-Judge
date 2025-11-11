import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Judge - Digital Justice System',
  description: 'AI-powered mock trial system for legal case analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
