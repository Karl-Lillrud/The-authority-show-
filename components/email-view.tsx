"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Search, X, Home, Menu, ChevronRight } from "lucide-react"
import { createSchedule } from "@/actions/schedule-actions"
import { useToast } from "@/components/ui/use-toast"

interface EmailViewProps {
  onNext: () => void
  onSelectEmail: (id: string) => void
}

interface Email {
  id: string
  title: string
  date: string
  preview: string
  count: string
}

export function EmailView({ onNext, onSelectEmail }: EmailViewProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    title: "",
    dateType: "recording",
    triggerDate: "",
    status: "active",
    delayType: "after",
    delayDays: 3,
    emailTemplate: "1",
    guest: true,
    team: false,
    host: false,
  })
  const { toast } = useToast()

  useEffect(() => {
    async function fetchEmails() {
      try {
        const response = await fetch("/api/emails")
        if (!response.ok) throw new Error("Failed to fetch emails")
        const data = await response.json()
        setEmails(data)
      } catch (error) {
        console.error("Error fetching emails:", error)
        toast({
          title: "Error",
          description: "Failed to load emails. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    fetchEmails()
  }, [toast])

  const handleEmailClick = (id: string) => {
    onSelectEmail(id)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
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

    const form = new FormData()
    Object.entries(formData).forEach(([key, value]) => {
      form.append(key, value.toString())
    })

    try {
      const result = await createSchedule(form)

      if (result.success) {
        toast({
          title: "Success",
          description: "Schedule created successfully",
        })
        onNext()
      } else {
        toast({
          title: "Error",
          description: result.error || "Failed to create schedule",
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error("Error creating schedule:", error)
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive",
      })
    }
  }

  return (
    <Card className="max-w-4xl mx-auto overflow-hidden">
      <div className="flex">
        {/* Left Panel */}
        <div className="w-1/2 border-r border-gray-100">
          <div className="p-4">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center">
                  <span className="text-orange-500 text-xs">+</span>
                </div>
                <h1 className="text-lg font-medium">Sclibed email</h1>
              </div>
              <button className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            {/* Search */}
            <div className="relative mb-6">
              <Search className="absolute left-3 top-2.5 text-gray-400" size={20} />
              <Input
                type="text"
                placeholder="Search inbox"
                className="pl-10 bg-white"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Email List */}
            <div className="space-y-4">
              {emails.map((email) => (
                <div
                  key={email.id}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleEmailClick(email.id)}
                >
                  <div className="w-10 h-10 rounded-full bg-gray-100 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900">{email.title}</h3>
                    <p className="text-sm text-gray-500">{email.date}</p>
                    <p className="text-sm text-gray-600 truncate">{email.preview}</p>
                  </div>
                  <span className="text-orange-400 text-sm">{email.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Navigation */}
          <div className="border-t border-gray-100 p-3 mt-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Home size={20} className="text-gray-500" />
              <span className="px-3 py-1 bg-orange-50 text-orange-500 rounded-full text-sm">Alspy</span>
              <span className="text-gray-500">Several effort</span>
            </div>
            <Menu size={20} className="text-gray-500" />
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-1/2 p-4">
          <div className="mb-6">
            <h2 className="text-lg font-medium mb-2">Creees Sccemenicy</h2>
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-gray-600 text-sm">With the Address (12 pm 3/1493-2022)</p>
              <Button className="bg-orange-400 hover:bg-orange-500 mt-4">Creatod vdristuale</Button>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-4">Create New Schedule</h3>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label className="required">Tocle</Label>
                <Input placeholder="Enter title" name="title" value={formData.title} onChange={handleInputChange} />
              </div>

              <div className="space-y-2">
                <Label className="required">Trigger Date</Label>
                <RadioGroup
                  defaultValue="recording"
                  className="flex space-x-4"
                  value={formData.dateType}
                  onValueChange={(value) => handleSelectChange("dateType", value)}
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="recording" id="recording" />
                    <Label htmlFor="recording">Recording Date</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="publishing" id="publishing" />
                    <Label htmlFor="publishing">Publishing Date</Label>
                  </div>
                </RadioGroup>
                <Input type="date" name="triggerDate" value={formData.triggerDate} onChange={handleInputChange} />
              </div>

              <div className="space-y-2">
                <Label className="required">Status</Label>
                <Select onValueChange={(value) => handleSelectChange("status", value)} defaultValue={formData.status}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="required">For wit Giles't cunemation</Label>
                <Input
                  placeholder=""
                  name="emailTemplate"
                  value={formData.emailTemplate}
                  onChange={handleInputChange}
                />
              </div>

              <div className="space-y-2">
                <Label className="required">Not fuindiver Parm</Label>
                <Input placeholder="" name="delayDays" value={formData.delayDays} onChange={handleInputChange} />
              </div>

              <div className="flex justify-between items-center">
                <Input
                  placeholder="Sor by-/UZSIP"
                  className="w-2/3"
                  name="delayType"
                  value={formData.delayType}
                  onChange={handleInputChange}
                />
                <span className="text-gray-500">Clacty</span>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="terms"
                  name="guest"
                  checked={formData.guest}
                  onCheckedChange={(checked) => setFormData((prev) => ({ ...prev, guest: checked || false }))}
                />
                <Label htmlFor="terms">Guest</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="team"
                  name="team"
                  checked={formData.team}
                  onCheckedChange={(checked) => setFormData((prev) => ({ ...prev, team: checked || false }))}
                />
                <Label htmlFor="team">Team</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="host"
                  name="host"
                  checked={formData.host}
                  onCheckedChange={(checked) => setFormData((prev) => ({ ...prev, host: checked || false }))}
                />
                <Label htmlFor="host">Host</Label>
              </div>

              <div className="flex justify-between items-center pt-6">
                <Button variant="outline" className="text-gray-500">
                  Footers
                </Button>
                <Button className="bg-orange-400 hover:bg-orange-500" type="submit">
                  Next
                  <ChevronRight className="ml-2" size={16} />
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Card>
  )
}

