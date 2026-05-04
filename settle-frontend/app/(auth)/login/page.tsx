"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { sendCode } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function validateEmail(value: string): string | null {
    if (!value.trim()) return "Email is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) return "Enter a valid email address.";
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const trimmed = email.trim();
    const emailErr = validateEmail(trimmed);
    if (emailErr) {
      setError(emailErr);
      return;
    }

    setLoading(true);
    const res = await sendCode(trimmed);
    setLoading(false);

    if (res.status === 0) {
      setError("Check your connection and try again.");
      return;
    }

    if (res.error) {
      setError(res.error);
      return;
    }

    router.push(`/verify?email=${encodeURIComponent(trimmed)}`);
  }

  return (
    <main className="min-h-dvh bg-gray-50 flex items-center justify-center px-5 py-6">
      <div className="w-full max-w-sm flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-10">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span className="text-[22px] font-bold text-[#1B4332] tracking-tight">Settle</span>
        </div>

        <h1 className="text-[28px] font-bold text-gray-900 leading-snug tracking-tight mb-2">
          Your agreements.<br />
          Witnessed. Sealed. Safe.
        </h1>
        <p className="text-[15px] text-gray-500 mb-9">Enter your email to get started.</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3" noValidate>
          <label htmlFor="email" className="text-sm font-medium text-gray-700">
            Email address
          </label>
          <input
            id="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError(""); }}
            disabled={loading}
            aria-describedby={error ? "email-error" : undefined}
            className="h-[52px] rounded-[10px] border border-gray-300 px-4 text-base text-gray-900 bg-white outline-none focus:border-[#1B4332] focus:ring-2 focus:ring-[#1B4332]/20 transition-colors w-full disabled:opacity-60"
          />

          {error && (
            <p id="email-error" className="text-[13px] text-red-600 m-0" role="alert">
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
