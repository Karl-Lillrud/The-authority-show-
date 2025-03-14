"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { TrashIcon } from "lucide-react"
import type { Task } from "@/types/task"
import { formatDate } from "@/lib/format-date"

interface TaskItemProps {
  task: Task
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}

export function TaskItem({ task, onToggle, onDelete }: TaskItemProps) {
  return (
    <li className="px-4 py-3 flex items-center gap-3 group">
      <Checkbox checked={task.completed} onCheckedChange={() => onToggle(task.id)} id={`task-${task.id}`} />
      <label
        htmlFor={`task-${task.id}`}
        className={`flex-1 cursor-pointer ${
          task.completed ? "text-slate-500 dark:text-slate-400 line-through" : "text-slate-700 dark:text-slate-200"
        }`}
      >
        <div>{task.text}</div>
        <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">{formatDate(task.createdAt)}</div>
      </label>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onDelete(task.id)}
        className="opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <TrashIcon className="h-4 w-4 text-slate-400 hover:text-red-500" />
        <span className="sr-only">Delete task</span>
      </Button>
    </li>
  )
}

