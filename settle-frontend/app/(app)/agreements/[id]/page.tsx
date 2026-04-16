"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import {
  getAgreement,
  downloadAgreementPDF,
  resendInvite,
  type Agreement,
} from "@/lib/api";
import { formatNaira, formatDate, getDaysRelative } from "@/lib/utils";
import StatusBadge from "@/components/StatusBadge";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function AgreementDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const rawUser =
    typeof window !== "undefined" ? localStorage.getItem("settle_user") : null;
  const user = rawUser ? JSON.parse(rawUser) : null;
  const userId: string = user?.id ?? "";

  const [agreement, setAgreement] = useState<Agreement | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendMsg, setResendMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const res = await getAgreement(id);

    if (res.status === 401) {
      router.push("/login?reason=session_expired");
      return;
    }
    if (res.status === 404) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    if (res.status === 403) {
      setForbidden(true);
      setLoading(false);
      return;
    }
    if (res.status === 0) {
      setError("Check your connection and try again.");
      setLoading(false);
      return;
    }
    if (res.error) {
      setError(res.error);
      setLoading(false);
      return;
    }

    setAgreement(res.data!);
    setLoading(false);
  }, [id, router]);

  useEffect(() => { load(); }, [load]);

  const handleResendInvite = async () => {
    setResending(true);
    setResendMsg(null);
    const res = await resendInvite(id);
    setResending(false);
    if (res.error) {
      setResendMsg(`Failed: ${res.error}`);
    } else {
      setResendMsg("Invite resent. Link expires in 72 hours.");
    }
  };

  const handleDownload = async () => {
    try { await downloadAgreementPDF(id); } catch { /* silent */ }
  };

  if (loading) return <LoadingSpinner className="mt-40" />;

  if (notFound) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <p className="text-gray-500 text-sm">Agreement not found.</p>
        <button onClick={() => router.push("/dashboard")} className="mt-4 text-sm text-green-600 font-medium">
          Back to dashboard
        </button>
      </div>
    );
  }

  if (forbidden) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <p className="text-gray-500 text-sm">You are not a party to this agreement.</p>
        <button onClick={() => router.push("/dashboard")} className="mt-4 text-sm text-green-600 font-medium">
          Back to dashboard
        </button>
      </div>
    );
  }

  if (error || !agreement) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
        <p className="text-red-500 text-sm">{error ?? "Something went wrong."}</p>
        <button onClick={load} className="mt-4 text-sm text-green-600 font-medium">Try again</button>
      </div>
    );
  }

  const isInitiator = agreement.initiator_id === userId;
  const { label, overdue } = getDaysRelative(agreement.repayment_date);
  const otherParty = isInitiator
    ? (agreement as Agreement & { counterparty_name?: string }).counterparty_name ?? agreement.counterparty_phone
    : (agreement as Agreement & { initiator_name?: string }).initiator_name ?? agreement.counterparty_phone;

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      {/* Header */}
      <div className="bg-white px-4 pt-12 pb-4 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} aria-label="Back">
            <ArrowLeft size={22} className="text-gray-700" />
          </button>
          <h1 className="flex-1 font-semibold text-gray-900 truncate">{agreement.title}</h1>
          <button onClick={handleDownload} aria-label="Download PDF">
            <Download size={20} className="text-gray-500" />
          </button>
        </div>
      </div>

      <div className="px-4 py-5 space-y-4">
        {/* Summary */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-3">
          <div className="flex items-center justify-between">
            <StatusBadge status={agreement.status} />
            <span className={overdue ? "text-sm font-medium text-red-600" : "text-sm text-gray-400"}>
              {label}
            </span>
          </div>

          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Amount</p>
            <p className="text-3xl font-bold text-gray-900 mt-0.5">{formatNaira(agreement.amount)}</p>
          </div>

          <div className="flex justify-between text-sm">
            <div>
              <p className="text-gray-400">Other party</p>
              <p className="font-medium text-gray-900">{otherParty}</p>
            </div>
            <div className="text-right">
              <p className="text-gray-400">Due date</p>
              <p className="font-medium text-gray-900">{formatDate(agreement.repayment_date)}</p>
            </div>
          </div>
        </div>

        {/* Terms */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Terms</p>
          <p className="text-sm text-gray-700 leading-relaxed">{agreement.terms}</p>
        </div>

        {/* Resend invite — only for initiator on pending agreements */}
        {isInitiator && agreement.status === "pending" && (
          <div className="bg-yellow-50 rounded-2xl p-4 border border-yellow-200">
            <p className="text-sm text-yellow-800 mb-3">
              Waiting for the other party to confirm. You can resend the invite if the link expired.
            </p>
            <button
              onClick={handleResendInvite}
              disabled={resending}
              className="flex items-center gap-2 text-sm font-semibold text-yellow-800 disabled:opacity-50"
            >
              <RefreshCw size={15} className={resending ? "animate-spin" : ""} />
              {resending ? "Resending…" : "Resend invite"}
            </button>
            {resendMsg && (
              <p className="mt-2 text-xs text-yellow-700">{resendMsg}</p>
            )}
          </div>
        )}

        {/* Payments CTA */}
        {agreement.status === "active" && (
          <button
            onClick={() => router.push(`/payments/${agreement.id}`)}
            className="w-full rounded-2xl bg-green-600 py-3.5 text-sm font-semibold text-white active:scale-[0.98] transition-transform"
          >
            View Payments
          </button>
        )}
      </div>
    </div>
  );
}
