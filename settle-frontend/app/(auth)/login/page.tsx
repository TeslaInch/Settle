"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { sendOTP } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const trimmed = phone.trim();
    if (!trimmed) {
      setError("Please enter your phone number.");
      return;
    }

    setLoading(true);
    const res = await sendOTP(trimmed);
    setLoading(false);

    if (res.error) {
      setError(res.error);
      return;
    }

    // Pass phone + is_new_user flag via query params (no router state in App Router)
    const params = new URLSearchParams({
      phone: trimmed,
      new_user: res.data?.is_new_user ? "1" : "0",
    });
    router.push(`/verify?${params.toString()}`);
  }

  return (
    <main style={styles.container}>
      <div style={styles.inner}>
        {/* Logo / Wordmark */}
        <div style={styles.logoWrap}>
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span style={styles.wordmark}>Settle</span>
        </div>

        <h1 style={styles.headline}>
          Your agreements.<br />
          Witnessed. Sealed. Safe.
        </h1>

        <form onSubmit={handleSubmit} style={styles.form} noValidate>
          <label htmlFor="phone" style={styles.label}>
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
            style={styles.input}
            disabled={loading}
            aria-describedby={error ? "phone-error" : undefined}
          />

          {error && (
            <p id="phone-error" style={styles.errorText} role="alert">
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
            {loading ? "Sending…" : "Send Code"}
          </button>
        </form>

        <p style={styles.footnote}>
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </main>
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
    gap: 0,
  },
  logoWrap: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 40,
  },
  wordmark: {
    fontSize: 22,
    fontWeight: 700,
    color: "#1B4332",
    letterSpacing: "-0.5px",
  },
  headline: {
    fontSize: 28,
    fontWeight: 700,
    color: "#111827",
    lineHeight: 1.3,
    marginBottom: 36,
    letterSpacing: "-0.5px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
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
    transition: "border-color 0.15s",
  },
  errorText: {
    fontSize: 13,
    color: "#DC2626",
    margin: 0,
  },
  button: {
    marginTop: 8,
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
  footnote: {
    marginTop: 24,
    fontSize: 12,
    color: "#9CA3AF",
    textAlign: "center",
    lineHeight: 1.6,
  },
};
