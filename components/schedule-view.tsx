"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle, Loader2 } from "lucide-react"
import { Badge } from "@/components/badge"
import { useToast } from "@/components/ui/use-toast"
import { deleteSchedule } from "@/actions/schedule-actions"

interface ScheduleViewProps {
  onBack: () => void
  onNext: () => void
  onSelectSchedule: (id: string) => void
}

interface Schedule {
  id: string
  title: string
  subtitle: string
  status: string
  dateType: string
  triggerDate: string
  nextRun: string
}

export function ScheduleView({ onBack, onNext, onSelectSchedule }: ScheduleViewProps) {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    async function fetchSchedules() {
      try {
        const response = await fetch("/api/schedules")
        if (!response.ok) throw new Error("Failed to fetch schedules")
        const data = await response.json()
        setSchedules(data)
      } catch (error) {
        console.error("Error fetching schedules:", error)
        toast({
          title: "Error",
          description: "Failed to load schedules. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSchedules()
  }, [toast])

  const handleScheduleClick = (id: string) => {
    setSelectedId(id)
    onSelectSchedule(id)
  }

  const handleDeleteSchedule = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent triggering the row click

    if (confirm("Are you sure you want to delete this schedule?")) {
      try {
        const result = await deleteSchedule(id)

        if (result.success) {
          setSchedules(schedules.filter((schedule) => schedule.id !== id))
          toast({
            title: "Success",
            description: "Schedule deleted successfully",
          })
        } else {
          toast({
            title: "Error",
            description: result.error || "Failed to delete schedule",
            variant: "destructive",
          })
        }
      } catch (error) {
        console.error("Error deleting schedule:", error)
        toast({
          title: "Error",
          description: "An unexpected error occurred",
          variant: "destructive",
        })
      }
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
      </div>
    )
  }

  return (
    <Card className="max-w-4xl mx-auto overflow-hidden">
      <div className="flex">
        {/* Left Panel */}
        <div className="w-1/2 border-r border-gray-100 p-4">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-xl font-medium">Schedule (rInib)</h1>
            <div className="flex gap-2">
              <Button variant="outline" className="text-orange-400 border-orange-200">
                Desig iin
              </Button>
              <Button className="bg-orange-400 hover:bg-orange-500">Chatel</Button>
            </div>
          </div>

          <div className="space-y-4">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className={`bg-white rounded-lg p-4 shadow-sm border border-gray-100 cursor-pointer hover:border-orange-200 ${
                  selectedId === schedule.id ? "border-orange-400" : ""
                }`}
                onClick={() => handleScheduleClick(schedule.id)}
              >
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-orange-500" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <h3 className="font-medium">{schedule.title}</h3>
                      <span className="text-sm text-gray-500">{schedule.status}</span>
                    </div>
                    <p className="text-sm text-gray-500">{schedule.subtitle}</p>
                    <div className="mt-3 space-y-2">
                      <div className="h-2 bg-gray-100 rounded-full w-full" />
                      <div className="h-2 bg-gray-100 rounded-full w-3/4" />
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="hover:bg-gray-100 rounded-full"
                    onClick={(e) => handleDeleteSchedule(schedule.id, e)}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="lucide lucide-trash"
                    >
                      <path d="M3 6h18" />
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                    </svg>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-1/2 p-4">
          <h2 className="text-xl font-medium mb-6">Stayies</h2>

          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span>Tine" • kular</span>
                <span className="px-3 py-1 bg-orange-50 text-orange-500 rounded-full text-sm">5:3D</span>
                <span>A/B</span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="mb-2">Dmd à Homos</h3>
                <div className="flex gap-2">
                  <Badge>2:018</Badge>
                  <Badge>fM</Badge>
                  <Badge>2:00/13</Badge>
                </div>
              </div>

              <div>
                <h3 className="mb-2">Bloans</h3>
                <div className="flex gap-2">
                  <Badge>SM</Badge>
                  <Badge>Sacarys</Badge>
                  <Badge>/N</Badge>
                </div>
              </div>

              <div>
                <h3 className="mb-2">Temiate! has</h3>
                <div className="flex gap-2">
                  <Badge>ABM</Badge>
                  <Badge>21/26:07/15</Badge>
                </div>
              </div>

              <div>
                <h3 className="mb-2">Tenbux</h3>
                <div className="h-2 bg-gray-100 rounded-full w-full mb-2" />
                <div className="h-2 bg-gray-100 rounded-full w-3/4" />
              </div>

              <div>
                <h3>Scloss crewrok Orteder</h3>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <Button variant="outline" onClick={onBack}>
                Next
              </Button>
              <Button className="bg-orange-400 hover:bg-orange-500" onClick={onNext}>
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

