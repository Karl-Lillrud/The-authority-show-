import type React from "react"
interface BadgeProps {
  children: React.ReactNode
}

export function Badge({ children }: BadgeProps) {
  return <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">{children}</span>
}

