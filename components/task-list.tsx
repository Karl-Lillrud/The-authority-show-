"use client"

import { TaskItem } from "@/components/task-item"
import type { Task } from "@/types/task"

interface TaskListProps {
  tasks: Task[]
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}

export function TaskList({ tasks, onToggle, onDelete }: TaskListProps) {
  return (
    <ul className="divide-y divide-slate-200 dark:divide-slate-700">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} onToggle={onToggle} onDelete={onDelete} />
      ))}
    </ul>
  )
}

