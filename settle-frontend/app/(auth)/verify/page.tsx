"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { verifyCode, sendCode } from "@/lib/api";

function VerifyForm() {
  const router = useRouter();
  const params = useSearchParams();

  const email = params.get("email") ?? "";
  const nameFromQuery = params.get("name") ?? "";
  const redirect = params.get("redirect") ?? "/dashboard";

  const emailDisplay =
    email.length > 24
      ? `${email.slice(0, 12)}…${email.slice(email.lastIndexOf("@"))}`
      : email;

  const [otp, setOtp] = useState<string[]>(Array(6).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (countdown <= 0) { setCanResend(true); return; }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const focusInput = (index: number) => inputRefs.current[index]?.focus();

  const handleOtpChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, "").slice(-1);
    const next = [...otp];
    next[index] = char;
    setOtp(next);
    if (char && index < 5) focusInput(index + 1);
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (otp[index]) {
        const next = [...otp]; next[index] = ""; setOtp(next);
      } else if (index > 0) {
        focusInput(index - 1);
      }
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 6) { setOtp(pasted.split("")); focusInput(5); }
    e.preventDefault();
  };

  const handleResend = useCallback(async () => {
    if (!canResend) return;
    setCanResend(false);
    setCountdown(60);
    setError("");
    await sendCode(email);
  }, [canResend, email]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const code = otp.join("");
    if (code.length < 6) {
      setError("Please enter the full 6-digit code.");
      return;
    }

    setLoading(true);
    // Pass name from query params — empty string for returning users, which
    // the backend treats as "no name provided" and skips profile creation.
    const res = await verifyCode(email, code, nameFromQuery || undefined);
    setLoading(false);

    // Backend says name is required — user is new but didn't enter a name.
    // Send them back to login with an explanatory message.
    if (res.status === 422 || res.error?.toLowerCase().includes("full_name")) {
      router.push(
        `/login?error=${encodeURIComponent("Please enter your name to sign up.")}&email=${encodeURIComponent(email)}`
      );
      return;
    }

    if (res.error) {
      setError(res.error);
      setOtp(Array(6).fill(""));
      focusInput(0);
      return;
    }

    if (res.data?.access_token) {
      localStorage.setItem("settle_token", res.data.access_token);

      // Fetch user profile and save to localStorage
      const meRes = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/auth/me`,
        { headers: { Authorization: `Bearer ${res.data.access_token}` } }
      );
      if (meRes.ok) {
        const user = await meRes.json();
        localStorage.setItem("settle_user", JSON.stringify(user));
      }
    }

    router.push(redirect);
  }

  return (
    <main className="min-h-dvh bg-gray-50 flex items-center justify-center px-5 py-6 lg:py-12">
      <div className="w-full max-w-sm md:max-w-md lg:max-w-lg flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-10">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span className="text-xl font-bold text-[#1B4332] tracking-tight">Settle</span>
        </div>

        <h1 className="text-[26px] font-bold text-gray-900 tracking-tight mb-2">
          Enter your code
        </h1>
        <p className="text-[15px] text-gray-500 leading-relaxed mb-8">
          We sent a 6-digit code to{" "}
          <strong className="text-gray-900">{emailDisplay}</strong>
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          {/* OTP boxes */}
          <div className="flex gap-2.5 justify-between" onPaste={handleOtpPaste}>
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleOtpChange(i, e.target.value)}
                onKeyDown={(e) => handleOtpKeyDown(i, e)}
                disabled={loading}
                aria-label={`Code digit ${i + 1}`}
                className={[
                  "flex-1 min-w-0 h-14 rounded-[10px] border text-center text-[22px] font-semibold text-gray-900 bg-white outline-none transition-colors",
                  error ? "border-red-500" : digit ? "border-[#1B4332]" : "border-gray-300",
                  "focus:border-[#1B4332] focus:ring-2 focus:ring-[#1B4332]/20",
                  loading ? "opacity-60" : "",
                ].join(" ")}
              />
            ))}
          </div>

          {error && (
            <p className="text-[13px] text-red-600 m-0" role="alert">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 h-[52px] rounded-[10px] bg-[#1B4332] text-white text-base font-semibold w-full transition-opacity disabled:opacity-70 disabled:cursor-not-allowed active:scale-[0.98]"
          >
            {loading ? "Verifying…" : "Verify & Continue"}
          </button>
        </form>

        {/* Resend */}
        <div className="mt-6 text-center">
          {canResend ? (
            <button
              onClick={handleResend}
              className="bg-transparent border-none text-[#1B4332] text-sm font-semibold cursor-pointer py-2 min-h-[48px]"
            >
              Resend code
            </button>
          ) : (
            <span className="text-sm text-gray-400">Resend code in {countdown}s</span>
          )}
        </div>
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyForm />
    </Suspense>
  );
}
