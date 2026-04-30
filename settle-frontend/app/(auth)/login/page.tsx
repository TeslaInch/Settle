"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { sendOTP } from "@/lib/api";
import { validateNigerianPhone } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sessionMsg, setSessionMsg] = useState("");

  useEffect(() => {
    if (searchParams.get("reason") === "session_expired") {
      setSessionMsg("Your session expired. Please log in again.");
    }
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const trimmed = phone.trim();
    const phoneErr = validateNigerianPhone(trimmed);
    if (phoneErr) {
      setError(phoneErr);
      return;
    }

    setLoading(true);
    const res = await sendOTP(trimmed);
    setLoading(false);

    if (res.status === 0) {
      setError("Check your connection and try again.");
      return;
    }

    if (res.error) {
      setError(res.error);
      return;
    }

    const redirect = searchParams.get("redirect") ?? "";
    const params = new URLSearchParams({ phone: trimmed });
    if (redirect) params.set("redirect", redirect);
    router.push(`/verify?${params.toString()}`);
  }

  return (
    <main className="min-h-dvh bg-gray-50 flex items-center justify-center px-5 py-6">
      <div className="w-full max-w-sm flex flex-col">
        {/* Logo / Wordmark */}
        <div className="flex items-center gap-2.5 mb-10">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span className="text-[22px] font-bold text-[#1B4332] tracking-tight">Settle</span>
        </div>

        <h1 className="text-[28px] font-bold text-gray-900 leading-snug tracking-tight mb-9">
          Your agreements.<br />
          Witnessed. Sealed. Safe.
        </h1>

        {sessionMsg && (
          <div
            className="bg-amber-50 border border-amber-300 rounded-lg px-3.5 py-2.5 text-[13px] text-amber-800 mb-4"
            role="alert"
          >
            {sessionMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3" noValidate>
          <label htmlFor="phone" className="text-sm font-medium text-gray-700">
            Phone number
          </label>
          <input
            id="phone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="+234 or 080..."
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={loading}
            aria-describedby={error ? "phone-error" : undefined}
            className="h-[52px] rounded-[10px] border border-gray-300 px-4 text-base text-gray-900 bg-white outline-none focus:border-[#1B4332] focus:ring-2 focus:ring-[#1B4332]/20 transition-colors w-full disabled:opacity-60"
          />

          {error && (
            <p id="phone-error" className="text-[13px] text-red-600 m-0" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 h-[52px] rounded-[10px] bg-[#1B4332] text-white text-base font-semibold w-full transition-opacity disabled:opacity-70 disabled:cursor-not-allowed active:scale-[0.98]"
          >
            {loading ? "Sending…" : "Send Code"}
          </button>
        </form>

        <p className="mt-6 text-xs text-gray-400 text-center leading-relaxed">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </main>
  );
}
