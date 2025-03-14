"use client"

import { Button } from "@/components/ui/button"

interface TaskFilterProps {
  currentFilter: "all" | "active" | "completed"
  onFilterChange: (filter: "all" | "active" | "completed") => void
}

export function TaskFilter({ currentFilter, onFilterChange }: TaskFilterProps) {
  return (
    <div className="flex gap-1">
      <Button
        variant={currentFilter === "all" ? "secondary" : "ghost"}
        size="sm"
        onClick={() => onFilterChange("all")}
        className="h-7 px-2 text-xs"
      >
        All
      </Button>
      <Button
        variant={currentFilter === "active" ? "secondary" : "ghost"}
        size="sm"
        onClick={() => onFilterChange("active")}
        className="h-7 px-2 text-xs"
      >
        Active
      </Button>
      <Button
        variant={currentFilter === "completed" ? "secondary" : "ghost"}
        size="sm"
        onClick={() => onFilterChange("completed")}
        className="h-7 px-2 text-xs"
      >
        Completed
      </Button>
    </div>
  )
}

