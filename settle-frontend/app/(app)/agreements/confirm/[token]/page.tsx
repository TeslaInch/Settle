"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle, Clock, XCircle } from "lucide-react";
import LoadingSpinner from "@/components/LoadingSpinner";

// This page is reached via the confirmation link sent to the counterparty.
// It reads the token from the URL, looks up the agreement, and confirms it.

interface AgreementPreview {
  id: string;
  title: string;
  amount: number;
  terms: string;
  initiator_name: string | null;
  initiator_phone: string;
  repayment_date: string;
}

type PageState =
  | { type: "loading" }
  | { type: "preview"; agreement: AgreementPreview }
  | { type: "confirming" }
  | { type: "success"; title: string }
  | { type: "expired"; initiator_name: string | null }
  | { type: "already_confirmed" }
  | { type: "error"; message: string }
  | { type: "not_found" };

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function ConfirmAgreementPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const [state, setState] = useState<PageState>({ type: "loading" });

  const authToken =
    typeof window !== "undefined" ? localStorage.getItem("settle_token") : null;

  useEffect(() => {
    if (!token) {
      setState({ type: "not_found" });
      return;
    }

    // Fetch agreement preview by token (public endpoint — no auth required)
    fetch(`${BASE_URL}/api/v1/agreements/by-token/${token}`)
      .then(async (res) => {
        if (res.status === 404) {
          setState({ type: "not_found" });
          return;
        }
        if (res.status === 410) {
          const data = await res.json().catch(() => ({}));
          setState({
            type: "expired",
            initiator_name: data?.initiator_name ?? null,
          });
          return;
        }
        if (res.status === 409) {
          setState({ type: "already_confirmed" });
          return;
        }
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          setState({ type: "error", message: data?.detail ?? "Something went wrong." });
          return;
        }
        const data = await res.json();
        setState({ type: "preview", agreement: data });
      })
      .catch(() => {
        setState({ type: "error", message: "Check your connection and try again." });
      });
  }, [token]);

  const handleConfirm = async () => {
    if (state.type !== "preview") return;

    if (!authToken) {
      // Not logged in — send to login, come back after
      router.push(`/login?redirect=/agreements/confirm/${token}`);
      return;
    }

    setState({ type: "confirming" });

    try {
      const res = await fetch(
        `${BASE_URL}/api/v1/agreements/${state.agreement.id}/confirm`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ confirmation_token: token }),
        }
      );

      const data = await res.json().catch(() => ({}));

      if (res.status === 409) {
        setState({ type: "already_confirmed" });
        return;
      }

      if (res.status === 400 && data?.detail?.includes("expired")) {
        setState({ type: "expired", initiator_name: null });
        return;
      }

      if (!res.ok) {
        setState({ type: "error", message: data?.detail ?? "Failed to confirm agreement." });
        return;
      }

      setState({ type: "success", title: state.agreement.title });
    } catch {
      setState({ type: "error", message: "Check your connection and try again." });
    }
  };

  if (state.type === "loading" || state.type === "confirming") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-3 text-sm text-gray-500">
            {state.type === "confirming" ? "Sealing agreement…" : "Loading…"}
          </p>
        </div>
      </div>
    );
  }

  if (state.type === "not_found") {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <XCircle size={40} className="text-gray-400 mb-4" />
        <h1 className="text-lg font-bold text-gray-900 mb-2">Link not found</h1>
        <p className="text-sm text-gray-500 max-w-[260px]">
          This confirmation link is invalid or has already been used.
        </p>
      </div>
    );
  }

  if (state.type === "expired") {
    const name = state.initiator_name ?? "the person who sent this";
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <Clock size={40} className="text-yellow-500 mb-4" />
        <h1 className="text-lg font-bold text-gray-900 mb-2">Link expired</h1>
        <p className="text-sm text-gray-500 max-w-[260px] leading-relaxed">
          This confirmation link has expired. Ask{" "}
          <span className="font-semibold text-gray-700">{name}</span> to resend it.
        </p>
      </div>
    );
  }

  if (state.type === "already_confirmed") {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <CheckCircle size={40} className="text-green-600 mb-4" />
        <h1 className="text-lg font-bold text-gray-900 mb-2">Already confirmed</h1>
        <p className="text-sm text-gray-500 max-w-[260px]">
          This agreement has already been sealed.
        </p>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-6 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white"
        >
          Go to dashboard
        </button>
      </div>
    );
  }

  if (state.type === "success") {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <CheckCircle size={48} className="text-green-600 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Agreement sealed</h1>
        <p className="text-sm text-gray-500 max-w-[260px] leading-relaxed">
          <span className="font-semibold text-gray-700">{state.title}</span> is now active.
          Both parties have confirmed.
        </p>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-6 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white"
        >
          View dashboard
        </button>
      </div>
    );
  }

  if (state.type === "error") {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <XCircle size={40} className="text-red-500 mb-4" />
        <h1 className="text-lg font-bold text-gray-900 mb-2">Something went wrong</h1>
        <p className="text-sm text-gray-500 max-w-[260px]">{state.message}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-6 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white"
        >
          Try again
        </button>
      </div>
    );
  }

  // Preview state
  const { agreement } = state;
  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      <div className="bg-white px-4 pt-12 md:pt-6 pb-5 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">Review Agreement</h1>
        <p className="text-sm text-gray-500 mt-1">
          {agreement.initiator_name ?? agreement.initiator_phone} wants you to confirm this.
        </p>
      </div>

      <div className="px-4 py-5 space-y-4">
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-3">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Title</p>
            <p className="font-semibold text-gray-900 mt-0.5">{agreement.title}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Amount</p>
            <p className="text-2xl font-bold text-gray-900 mt-0.5">
              ₦{Number(agreement.amount).toLocaleString("en-NG")}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Repayment date</p>
            <p className="font-medium text-gray-900 mt-0.5">
              {new Date(agreement.repayment_date).toLocaleDateString("en-NG", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Terms</p>
            <p className="text-sm text-gray-700 mt-0.5 leading-relaxed">{agreement.terms}</p>
          </div>
        </div>

        <p className="text-xs text-gray-400 text-center px-4">
          By confirming, you agree to the terms above. This agreement will be sealed and cannot be changed.
        </p>

        <button
          onClick={handleConfirm}
          className="w-full rounded-2xl bg-green-600 py-3.5 text-sm font-semibold text-white active:scale-[0.98] transition-transform"
        >
          Confirm &amp; Seal Agreement
        </button>
      </div>
    </div>
  );
}
