export function formatDate(date: Date): string {
  if (!(date instanceof Date)) {
    date = new Date(date)
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date)
}

