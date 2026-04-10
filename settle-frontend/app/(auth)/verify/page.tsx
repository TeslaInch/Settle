"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { verifyOTP, sendOTP } from "@/lib/api";

function VerifyForm() {
  const router = useRouter();
  const params = useSearchParams();

  const phone = params.get("phone") ?? "";
  const isNewUser = params.get("new_user") === "1";

  const last4 = phone.slice(-4);

  const [otp, setOtp] = useState<string[]>(Array(6).fill(""));
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) {
      setCanResend(true);
      return;
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const focusInput = (index: number) => {
    inputRefs.current[index]?.focus();
  };

  const handleOtpChange = (index: number, value: string) => {
    const char = value.replace(/\D/g, "").slice(-1);
    const next = [...otp];
    next[index] = char;
    setOtp(next);
    if (char && index < 5) {
      focusInput(index + 1);
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (otp[index]) {
        const next = [...otp];
        next[index] = "";
        setOtp(next);
      } else if (index > 0) {
        focusInput(index - 1);
      }
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(""));
      focusInput(5);
    }
    e.preventDefault();
  };

  const handleResend = useCallback(async () => {
    if (!canResend) return;
    setCanResend(false);
    setCountdown(60);
    setError("");
    await sendOTP(phone);
  }, [canResend, phone]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const code = otp.join("");
    if (code.length < 6) {
      setError("Please enter the full 6-digit code.");
      return;
    }
    if (isNewUser && !fullName.trim()) {
      setError("Please enter your full name.");
      return;
    }

    setLoading(true);
    const res = await verifyOTP(phone, code, isNewUser ? fullName.trim() : undefined);
    setLoading(false);

    if (res.error) {
      setError(res.error);
      setOtp(Array(6).fill(""));
      focusInput(0);
      return;
    }

    if (res.data?.access_token) {
      localStorage.setItem("token", res.data.access_token);
    }

    router.push("/dashboard");
  }

  return (
    <main style={styles.container}>
      <div style={styles.inner}>
        {/* Logo */}
        <div style={styles.logoWrap}>
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span style={styles.wordmark}>Settle</span>
        </div>

        <h1 style={styles.heading}>Enter your code</h1>
        <p style={styles.subheading}>
          We sent a 6-digit code to the number ending in{" "}
          <strong style={{ color: "#111827" }}>••••{last4}</strong>
        </p>

        <form onSubmit={handleSubmit} style={styles.form} noValidate>
          {/* Full name — only for new users */}
          {isNewUser && (
            <div style={styles.fieldGroup}>
              <label htmlFor="full-name" style={styles.label}>
                Full name
              </label>
              <input
                id="full-name"
                type="text"
                autoComplete="name"
                placeholder="Ada Okonkwo"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                style={styles.input}
                disabled={loading}
              />
            </div>
          )}

          {/* OTP boxes */}
          <div style={styles.otpRow} onPaste={handleOtpPaste}>
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
                style={{
                  ...styles.otpBox,
                  borderColor: error ? "#DC2626" : digit ? "#1B4332" : "#D1D5DB",
                }}
                disabled={loading}
                aria-label={`OTP digit ${i + 1}`}
              />
            ))}
          </div>

          {error && (
            <p style={styles.errorText} role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.button,
              opacity: loading ? 0.7 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Verifying…" : "Verify & Continue"}
          </button>
        </form>

        {/* Resend */}
        <div style={styles.resendWrap}>
          {canResend ? (
            <button onClick={handleResend} style={styles.resendBtn}>
              Resend code
            </button>
          ) : (
            <span style={styles.resendCountdown}>
              Resend code in {countdown}s
            </span>
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

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100dvh",
    backgroundColor: "#F9FAFB",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px 20px",
    fontFamily: "'Inter', sans-serif",
  },
  inner: {
    width: "100%",
    maxWidth: 400,
    display: "flex",
    flexDirection: "column",
  },
  logoWrap: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 40,
  },
  wordmark: {
    fontSize: 20,
    fontWeight: 700,
    color: "#1B4332",
    letterSpacing: "-0.5px",
  },
  heading: {
    fontSize: 26,
    fontWeight: 700,
    color: "#111827",
    marginBottom: 8,
    letterSpacing: "-0.4px",
  },
  subheading: {
    fontSize: 15,
    color: "#6B7280",
    marginBottom: 32,
    lineHeight: 1.5,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  label: {
    fontSize: 14,
    fontWeight: 500,
    color: "#374151",
  },
  input: {
    height: 52,
    borderRadius: 10,
    border: "1.5px solid #D1D5DB",
    padding: "0 16px",
    fontSize: 16,
    color: "#111827",
    backgroundColor: "#fff",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  },
  otpRow: {
    display: "flex",
    gap: 10,
    justifyContent: "space-between",
  },
  otpBox: {
    flex: 1,
    height: 56,
    borderRadius: 10,
    border: "1.5px solid #D1D5DB",
    textAlign: "center",
    fontSize: 22,
    fontWeight: 600,
    color: "#111827",
    backgroundColor: "#fff",
    outline: "none",
    transition: "border-color 0.15s",
    minWidth: 0,
  },
  errorText: {
    fontSize: 13,
    color: "#DC2626",
    margin: 0,
  },
  button: {
    marginTop: 4,
    height: 52,
    borderRadius: 10,
    backgroundColor: "#1B4332",
    color: "#fff",
    fontSize: 16,
    fontWeight: 600,
    border: "none",
    width: "100%",
    transition: "opacity 0.15s",
  },
  resendWrap: {
    marginTop: 24,
    textAlign: "center",
  },
  resendBtn: {
    background: "none",
    border: "none",
    color: "#1B4332",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    padding: "8px 0",
    minHeight: 48,
  },
  resendCountdown: {
    fontSize: 14,
    color: "#9CA3AF",
  },
};
