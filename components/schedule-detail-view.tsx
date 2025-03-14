"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { updateSchedule } from "@/actions/schedule-actions"

interface ScheduleDetailViewProps {
  onBack: () => void
  scheduleId: string | null
}

interface Schedule {
  id: string
  title: string
  subtitle: string
  status: string
  dateType: string
  triggerDate: string
  recipients: string[]
  emailTemplate: string
  delayType: string
  delayDays: number
  createdAt: string
  updatedAt: string
  nextRun: string
}

export function ScheduleDetailView({ onBack, scheduleId }: ScheduleDetailViewProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [schedule, setSchedule] = useState<Schedule | null>(null)
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    title: "",
    subtitle: "",
    status: "",
  })
  const { toast } = useToast()

  useEffect(() => {
    async function fetchSchedule() {
      if (!scheduleId) {
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`/api/schedules/${scheduleId}`)
        if (!response.ok) throw new Error("Failed to fetch schedule")
        const data = await response.json()
        setSchedule(data)
        setFormData({
          title: data.title,
          subtitle: data.subtitle || "",
          status: data.status,
        })
      } catch (error) {
        console.error("Error fetching schedule:", error)
        toast({
          title: "Error",
          description: "Failed to load schedule details. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSchedule()
  }, [scheduleId, toast])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!scheduleId) return

    const form = new FormData()
    Object.entries(formData).forEach(([key, value]) => {
      form.append(key, value.toString())
    })

    try {
      const result = await updateSchedule(scheduleId, form)

      if (result.success) {
        setSchedule({
          ...schedule!,
          ...formData,
          updatedAt: new Date().toISOString(),
        })
        setIsEditing(false)
        toast({
          title: "Success",
          description: "Schedule updated successfully",
        })
      } else {
        toast({
          title: "Error",
          description: result.error || "Failed to update schedule",
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Error updating schedule:", error)
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-orange-400" />
      </div>
    )
  }

  if (!schedule) {
    return (
      <div className="text-center p-8">
        <h2 className="text-xl font-medium mb-2">Schedule not found</h2>
        <p className="text-gray-500 mb-4">The requested schedule could not be found.</p>
        <Button onClick={onBack}>Go Back</Button>
      </div>
    )
  }

  return (
    <Card className="max-w-4xl mx-auto overflow-hidden">
      <div className="flex">
        {/* Left Panel */}
        <div className="w-1/2 border-r border-gray-100 p-4">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-xl font-medium">Schedule Details</h1>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="text-orange-400 border-orange-200"
                onClick={() => setIsEditing(!isEditing)}
              >
                {isEditing ? "Cancel" : "Edit"}
              </Button>
              {isEditing && (
                <Button className="bg-orange-400 hover:bg-orange-500" onClick={handleSubmit}>
                  Save
                </Button>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Schedule Name</Label>
              {isEditing ? (
                <Input name="title" value={formData.title} onChange={handleInputChange} />
              ) : (
                <div className="p-2 bg-gray-50 rounded">{schedule.title}</div>
              )}
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              {isEditing ? (
                <Textarea name="subtitle" value={formData.subtitle} onChange={handleInputChange} />
              ) : (
                <div className="p-2 bg-gray-50 rounded">{schedule.subtitle}</div>
              )}
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              {isEditing ? (
                <Select value={formData.status} onValueChange={(value) => handleSelectChange("status", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <div className="p-2 bg-gray-50 rounded">{schedule.status}</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-1/2 p-4">
          <h2 className="text-xl font-medium mb-6">Timeline</h2>

          <div className="space-y-6">
            <div className="space-y-4">
              <div>
                <h3 className="mb-2 text-sm text-gray-600">Created</h3>
                <Badge>{schedule.createdAt}</Badge>
              </div>

              <div>
                <h3 className="mb-2 text-sm text-gray-600">Last Modified</h3>
                <Badge>{schedule.updatedAt}</Badge>
              </div>

              <div>
                <h3 className="mb-2 text-sm text-gray-600">Next Run</h3>
                <Badge>{schedule.nextRun}</Badge>
              </div>

              {isEditing && (
                <div>
                  <h3 className="mb-2 text-sm text-gray-600">Schedule Type</h3>
                  <Select defaultValue="automatic">
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="automatic">Automatic</SelectItem>
                      <SelectItem value="manual">Manual</SelectItem>
                      <SelectItem value="recurring">Recurring</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="pt-4 flex justify-end">
              <Button variant="outline" onClick={onBack} className="mr-2">
                Back
              </Button>
              <Button className="bg-orange-400 hover:bg-orange-500">{isEditing ? "Update" : "Run Now"}</Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

