"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { sendCode } from "@/lib/api";
import { Suspense } from "react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Pre-fill error message if redirected back from verify page
  const redirectError = searchParams.get("error") ?? "";

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(redirectError);

  function validateEmail(value: string): string | null {
    if (!value.trim()) return "Email is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()))
      return "Enter a valid email address.";
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const trimmedEmail = email.trim();
    const emailErr = validateEmail(trimmedEmail);
    if (emailErr) {
      setError(emailErr);
      return;
    }

    setLoading(true);
    const res = await sendCode(trimmedEmail);
    setLoading(false);

    if (res.status === 0) {
      setError("Check your connection and try again.");
      return;
    }

    if (res.error) {
      setError(res.error);
      return;
    }

    const params = new URLSearchParams({ email: trimmedEmail });
    if (fullName.trim()) params.set("name", fullName.trim());

    const redirect = searchParams.get("redirect");
    if (redirect) params.set("redirect", redirect);

    router.push(`/verify?${params.toString()}`);
  }

  return (
    <main className="min-h-dvh bg-gray-50 flex items-center justify-center px-5 py-6 lg:py-12">
      <div className="w-full max-w-sm md:max-w-md lg:max-w-lg flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-10">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <text
              x="16"
              y="22"
              textAnchor="middle"
              fill="white"
              fontSize="20"
              fontWeight="bold"
              fontFamily="Helvetica, Arial, sans-serif"
            >S</text>
          </svg>
          <span className="text-[22px] font-bold text-[#1B4332] tracking-tight">Settle</span>
        </div>

        <h1 className="text-[28px] font-bold text-gray-900 leading-snug tracking-tight mb-2">
          Your agreements.<br />
          Witnessed. Sealed. Safe.
        </h1>
        <p className="text-[15px] text-gray-500 mb-8">Enter your email to get started.</p>

        {error && (
          <div
            className="bg-amber-50 border border-amber-300 rounded-lg px-3.5 py-2.5 text-[13px] text-amber-800 mb-4"
            role="alert"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          {/* Email */}
          <div className="flex flex-col gap-1.5">
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
              className="h-[52px] rounded-[10px] border border-gray-300 px-4 text-base text-gray-900 bg-white outline-none focus:border-[#1B4332] focus:ring-2 focus:ring-[#1B4332]/20 transition-colors w-full disabled:opacity-60"
            />
          </div>

          {/* Full name — optional, for new users */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="full-name" className="text-sm font-medium text-gray-700">
              Your name{" "}
              <span className="text-gray-400 font-normal">(new users only)</span>
            </label>
            <input
              id="full-name"
              type="text"
              autoComplete="name"
              placeholder="Ada Okonkwo"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
              className="h-[52px] rounded-[10px] border border-gray-300 px-4 text-base text-gray-900 bg-white outline-none focus:border-[#1B4332] focus:ring-2 focus:ring-[#1B4332]/20 transition-colors w-full disabled:opacity-60"
            />
            <p className="text-[12px] text-gray-400">
              Already signed up? Leave this blank.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-1 h-[52px] rounded-[10px] bg-[#1B4332] text-white text-base font-semibold w-full transition-opacity disabled:opacity-70 disabled:cursor-not-allowed active:scale-[0.98]"
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

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
