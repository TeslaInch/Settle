const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface SendCodeResponse {
  message: string;
}

export interface VerifyCodeResponse {
  access_token: string;
  token_type: string;
  is_new_user: boolean;
}

// ── Agreements ────────────────────────────────────────────────────────────────

export interface Agreement {
  id: string;
  title: string;
  amount: number;
  terms: string;
  initiator_id: string;
  counterparty_id: string | null;
  counterparty_email: string;
  repayment_date: string;
  status: "pending" | "active" | "completed" | "overdue" | "cancelled";
  seal_hash: string | null;
  sealed_at: string | null;
  created_at: string;
  other_party_name?: string | null;
}

export interface CreateAgreementPayload {
  title: string;
  amount: number;
  terms: string;
  counterparty_email: string;
  repayment_date: string;
}

// ── Payments ──────────────────────────────────────────────────────────────────

export interface Payment {
  id: string;
  agreement_id: string;
  payer_id: string;
  amount: number;
  note: string | null;
  logged_at: string;
  confirmed_by_receiver: boolean;
  confirmed_at: string | null;
  disputed: boolean;
  disputed_at: string | null;
  dispute_reason: string | null;
}

// ── Notifications ─────────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  agreement_id: string | null;
  type: string;
  message: string;
  read: boolean;
  sent_at: string;
}

export interface LogPaymentPayload {
  amount: number;
  note?: string;
}

// ── HTTP helper ───────────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("settle_token");
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      return {
        status: res.status,
        error: json?.detail ?? json?.message ?? "Something went wrong.",
      };
    }

    return { status: res.status, data: json as T };
  } catch {
    return { status: 0, error: "Network error. Please check your connection." };
  }
}

// ── Auth endpoints ────────────────────────────────────────────────────────────

export async function sendCode(
  email: string
): Promise<ApiResponse<SendCodeResponse>> {
  return apiRequest<SendCodeResponse>("/api/v1/auth/send-code", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function verifyCode(
  email: string,
  code: string,
  full_name?: string
): Promise<ApiResponse<VerifyCodeResponse>> {
  return apiRequest<VerifyCodeResponse>("/api/v1/auth/verify-code", {
    method: "POST",
    body: JSON.stringify({ email, code, full_name }),
  });
}

// ── Agreement endpoints ───────────────────────────────────────────────────────

export async function getAgreements(): Promise<ApiResponse<Agreement[]>> {
  return apiRequest<Agreement[]>("/api/v1/agreements");
}

export async function getAgreement(id: string): Promise<ApiResponse<Agreement>> {
  return apiRequest<Agreement>(`/api/v1/agreements/${id}`);
}

export async function createAgreement(
  payload: CreateAgreementPayload
): Promise<ApiResponse<Agreement>> {
  return apiRequest<Agreement>("/api/v1/agreements", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function downloadAgreementPDF(agreementId: string): Promise<void> {
  const token = getToken();
  const res = await fetch(
    `${BASE_URL}/api/v1/agreements/${agreementId}/pdf`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  if (!res.ok) throw new Error("Failed to download PDF.");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `settle-agreement-${agreementId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Payment endpoints ─────────────────────────────────────────────────────────

export async function getPayments(
  agreementId: string
): Promise<ApiResponse<Payment[]>> {
  return apiRequest<Payment[]>(`/api/v1/agreements/${agreementId}/payments`);
}

export async function logPayment(
  agreementId: string,
  payload: LogPaymentPayload
): Promise<ApiResponse<Payment>> {
  return apiRequest<Payment>(`/api/v1/agreements/${agreementId}/payments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function confirmPayment(
  paymentId: string
): Promise<ApiResponse<Payment>> {
  return apiRequest<Payment>(`/api/v1/payments/${paymentId}/confirm`, {
    method: "PATCH",
  });
}

export async function disputePayment(
  paymentId: string,
  reason: string
): Promise<ApiResponse<Payment>> {
  return apiRequest<Payment>(`/api/v1/payments/${paymentId}/dispute`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function resendInvite(
  agreementId: string
): Promise<ApiResponse<{ message: string; expires_in_hours: number }>> {
  return apiRequest(`/api/v1/agreements/${agreementId}/resend-invite`, {
    method: "POST",
  });
}

// ── Notification endpoints ────────────────────────────────────────────────────

export async function getNotifications(): Promise<ApiResponse<Notification[]>> {
  return apiRequest("/api/v1/notifications");
}

export async function getUnreadCount(): Promise<ApiResponse<{ count: number }>> {
  return apiRequest("/api/v1/notifications/unread-count");
}

export async function markAsRead(id: string): Promise<ApiResponse<any>> {
  return apiRequest(`/api/v1/notifications/${id}/read`, {
    method: "POST",
  });
}

export async function markAllRead(): Promise<ApiResponse<any>> {
  return apiRequest("/api/v1/notifications/read-all", {
    method: "POST",
  });
}
