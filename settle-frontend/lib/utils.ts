import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNaira(amount: number): string {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  return new Intl.DateTimeFormat("en-NG", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(dateStr));
}

export function getDaysRelative(dateStr: string): { label: string; overdue: boolean } {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const due = new Date(dateStr);
  due.setHours(0, 0, 0, 0);
  const diff = Math.round((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (diff === 0) return { label: "Due today", overdue: false };
  if (diff > 0) return { label: `${diff} day${diff === 1 ? "" : "s"} left`, overdue: false };
  return { label: `${Math.abs(diff)} day${Math.abs(diff) === 1 ? "" : "s"} overdue`, overdue: true };
}

export function getGreeting(name: string): string {
  const hour = new Date().getHours();
  if (hour < 12) return `Good morning, ${name}`;
  if (hour < 17) return `Good afternoon, ${name}`;
  return `Good evening, ${name}`;
}

//function for exporting first name.

export function getFirstName(fullName: string | null | undefined): string {
  if (!fullName) return "there";
  return fullName.trim().split(" ")[0];
}

//utils file before later updates 



export function markFirstAgreementCreated(): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("settle_has_agreement", "1");
  }
}

// ── Form validation ───────────────────────────────────────────────────────────

export function validateNigerianPhone(value: string): string | null {
  const v = value.trim().replace(/\s|-/g, "");
  const valid =
    (v.startsWith("+234") && v.length === 14 && /^\d+$/.test(v.slice(4))) ||
    (v.startsWith("234") && v.length === 13 && /^\d+$/.test(v.slice(3))) ||
    (v.startsWith("0") && v.length === 11 && /^\d+$/.test(v.slice(1)));
  return valid ? null : "Enter a valid Nigerian phone number (e.g. 08012345678)";
}

export function validateAmount(value: string): string | null {
  const n = parseFloat(value);
  if (isNaN(n) || n <= 0) return "Enter a positive amount";
  return null;
}

export function validateFutureDate(value: string): string | null {
  if (!value) return "Repayment date is required";
  const d = new Date(value);
  if (isNaN(d.getTime())) return "Enter a valid date";
  if (d <= new Date()) return "Repayment date must be in the future";
  return null;
}

export function validateTerms(value: string): string | null {
  if (value.trim().length < 20) return "Terms must be at least 20 characters";
  return null;
}
