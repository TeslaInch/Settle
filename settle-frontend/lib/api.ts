const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface SendOTPResponse {
  message: string;
  is_new_user: boolean;
}

export interface VerifyOTPResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    phone: string;
    full_name: string | null;
  };
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
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
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers,
    });

    const json = await res.json().catch(() => ({}));

    if (!res.ok) {
      return {
        status: res.status,
        error: json?.detail ?? json?.message ?? "Something went wrong",
      };
    }

    return { status: res.status, data: json as T };
  } catch {
    return { status: 0, error: "Network error. Please check your connection." };
  }
}

export async function sendOTP(phone: string): Promise<ApiResponse<SendOTPResponse>> {
  return apiRequest<SendOTPResponse>("/auth/send-otp", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOTP(
  phone: string,
  otp: string,
  fullName?: string
): Promise<ApiResponse<VerifyOTPResponse>> {
  return apiRequest<VerifyOTPResponse>("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ phone, otp, full_name: fullName }),
  });
}
