import { cn } from "@/lib/utils";

type Status = "pending" | "active" | "completed" | "overdue" | "cancelled";

const styles: Record<Status, string> = {
  pending:   "bg-yellow-100 text-yellow-800",
  active:    "bg-green-100  text-green-800",
  completed: "bg-blue-100   text-blue-800",
  overdue:   "bg-red-100    text-red-700",
  cancelled: "bg-gray-100   text-gray-500",
};

const labels: Record<Status, string> = {
  pending:   "Pending",
  active:    "Active",
  completed: "Completed",
  overdue:   "Overdue",
  cancelled: "Cancelled",
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        styles[status]
      )}
    >
      {labels[status]}
    </span>
  );
}
