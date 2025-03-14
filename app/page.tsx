"use client"

import { useState } from "react"
import { EmailView } from "@/components/email-view"
import { ScheduleView } from "@/components/schedule-view"
import { ScheduleDetailView } from "@/components/schedule-detail-view"

type View = "email" | "schedule" | "detail"

export default function EmailScheduler() {
  const [currentView, setCurrentView] = useState<View>("email")
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null)
  const [selectedSchedule, setSelectedSchedule] = useState<string | null>(null)

  const handleNavigate = (view: View) => {
    setCurrentView(view)
  }

  return (
    <div className="min-h-screen bg-gray-100/50 p-4">
      {currentView === "email" && (
        <EmailView onNext={() => handleNavigate("schedule")} onSelectEmail={setSelectedEmail} />
      )}

      {currentView === "schedule" && (
        <ScheduleView
          onBack={() => handleNavigate("email")}
          onNext={() => handleNavigate("detail")}
          onSelectSchedule={setSelectedSchedule}
        />
      )}

      {currentView === "detail" && (
        <ScheduleDetailView onBack={() => handleNavigate("schedule")} scheduleId={selectedSchedule} />
      )}
    </div>
  )
}

