const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface SendOTPResponse {
  message: string;
  phone_number: string;
  pin_id: string;
}

export interface VerifyOTPResponse {
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
  counterparty_phone: string;
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
  counterparty_phone: string;
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

export async function sendOTP(
  phone_number: string
): Promise<ApiResponse<SendOTPResponse>> {
  return apiRequest<SendOTPResponse>("/api/v1/auth/send-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number }),
  });
}

export async function verifyOTP(
  phone_number: string,
  otp_code: string,
  pin_id: string,
  full_name?: string
): Promise<ApiResponse<VerifyOTPResponse>> {
  return apiRequest<VerifyOTPResponse>("/api/v1/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone_number, otp_code, pin_id, full_name }),
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
