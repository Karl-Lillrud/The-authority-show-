"use server"

import {
  createSchedule as dbCreateSchedule,
  updateSchedule as dbUpdateSchedule,
  deleteSchedule as dbDeleteSchedule,
} from "@/lib/db"
import { revalidatePath } from "next/cache"

export async function createSchedule(formData: FormData) {
  try {
    const title = formData.get("title") as string
    const dateType = formData.get("dateType") as string // 'publishing' eller 'recalling'
    const triggerDate = new Date(formData.get("triggerDate") as string)
    const status = formData.get("status") as string
    const delayType = formData.get("delayType") as string // 'before' eller 'after'
    const delayDays = Number.parseInt(formData.get("delayDays") as string)
    const emailTemplate = formData.get("emailTemplate") as string

    // Hantera mottagare (checkboxes)
    const recipients = []
    if (formData.get("guest")) recipients.push("guest")
    if (formData.get("team")) recipients.push("team")
    if (formData.get("host")) recipients.push("host")

    // Skapa data-objekt för databasen
    const data = {
      title,
      date_type: dateType,
      trigger_date: triggerDate,
      status,
      delay_type: delayType,
      delay_days: delayDays,
      email_template: emailTemplate,
      recipients,
    }

    const result = await dbCreateSchedule(data)

    revalidatePath("/") // Uppdatera sidan för att visa nya data

    return { success: true, schedule: result }
  } catch (error) {
    console.error("Error creating schedule:", error)
    return { success: false, error: "Failed to create schedule" }
  }
}

export async function updateSchedule(id: string, formData: FormData) {
  try {
    const title = formData.get("title") as string
    const subtitle = formData.get("subtitle") as string
    const status = formData.get("status") as string

    const data = {
      title,
      subtitle,
      status,
    }

    await dbUpdateSchedule(id, data)

    revalidatePath("/") // Uppdatera sidan för att visa nya data

    return { success: true }
  } catch (error) {
    console.error("Error updating schedule:", error)
    return { success: false, error: "Failed to update schedule" }
  }
}

export async function deleteSchedule(id: string) {
  try {
    await dbDeleteSchedule(id)

    revalidatePath("/") // Uppdatera sidan för att visa nya data

    return { success: true }
  } catch (error) {
    console.error("Error deleting schedule:", error)
    return { success: false, error: "Failed to delete schedule" }
  }
}

