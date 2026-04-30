"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Receipt } from "lucide-react";

import {
  confirmPayment,
  downloadAgreementPDF,
  getAgreement,
  getPayments,
  logPayment,
  type Agreement,
  type Payment,
} from "@/lib/api";
import { formatNaira } from "@/lib/utils";
import BottomSheet from "@/components/BottomSheet";
import EmptyState from "@/components/EmptyState";
import LoadingSpinner from "@/components/LoadingSpinner";
import PaymentItem from "@/components/PaymentItem";

export default function PaymentsPage() {
  const { agreementId } = useParams<{ agreementId: string }>();
  const router = useRouter();

  const rawUser =
    typeof window !== "undefined" ? localStorage.getItem("settle_user") : null;
  const user = rawUser ? JSON.parse(rawUser) : null;
  const userId: string = user?.id ?? "";

  const [agreement, setAgreement] = useState<Agreement | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Log payment sheet
  const [sheetOpen, setSheetOpen] = useState(false);
  const [logAmount, setLogAmount] = useState("");
  const [logNote, setLogNote] = useState("");
  const [logging, setLogging] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);

  // Confirm state
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    const [agRes, pmRes] = await Promise.all([
      getAgreement(agreementId),
      getPayments(agreementId),
    ]);

    if (agRes.error) { setError(agRes.error); setLoading(false); return; }
    if (pmRes.error) { setError(pmRes.error); setLoading(false); return; }

    setAgreement(agRes.data!);
    setPayments(pmRes.data ?? []);
    setLoading(false);
  }, [agreementId]);

  useEffect(() => { load(); }, [load]);

  // Derived values
  const totalPaid = payments
    .filter((p) => p.confirmed_by_receiver)
    .reduce((sum, p) => sum + p.amount, 0);
  const remaining = agreement ? Math.max(0, agreement.amount - totalPaid) : 0;
  const paidPercent = agreement
    ? Math.min(100, Math.round((totalPaid / agreement.amount) * 100))
    : 0;

  const isReceiver = agreement?.counterparty_id === userId;

  // Open sheet pre-filled with remaining
  const openLogSheet = () => {
    setLogAmount(remaining > 0 ? String(remaining) : "");
    setLogNote("");
    setLogError(null);
    setSheetOpen(true);
  };

  const handleLogPayment = async () => {
    const amount = parseFloat(logAmount);
    if (!amount || amount <= 0) {
      setLogError("Enter a valid amount.");
      return;
    }
    setLogging(true);
    setLogError(null);

    const res = await logPayment(agreementId, {
      amount,
      note: logNote.trim() || undefined,
    });

    setLogging(false);

    if (res.error) {
      setLogError(res.error);
      return;
    }

    setSheetOpen(false);
    load();
  };

  const handleConfirm = async (paymentId: string) => {
    setConfirmingId(paymentId);
    await confirmPayment(paymentId);
    setConfirmingId(null);
    load();
  };

  const handleDownloadPDF = async () => {
    try {
      await downloadAgreementPDF(agreementId);
    } catch {
      // silently fail — user will notice nothing downloaded
    }
  };

  if (loading) return <LoadingSpinner className="mt-40" />;

  if (error || !agreement) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-4">
        <p className="text-sm text-red-500 text-center">{error ?? "Agreement not found."}</p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-green-600 font-medium">
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      {/* Top bar */}
      <div className="bg-white px-4 pt-12 md:pt-6 pb-4 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} aria-label="Back">
            <ArrowLeft size={22} className="text-gray-700" />
          </button>
          <h1 className="flex-1 font-semibold text-gray-900 truncate">{agreement.title}</h1>
          <button onClick={handleDownloadPDF} aria-label="Download PDF">
            <Download size={20} className="text-gray-500" />
          </button>
        </div>
      </div>

      <div className="px-4 py-5 space-y-5">
        {/* Summary card */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-3">
          <div className="flex justify-between text-sm text-gray-500">
            <span>Total amount</span>
            <span className="font-semibold text-gray-900">{formatNaira(agreement.amount)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-500">
            <span>Amount paid</span>
            <span className="font-semibold text-green-600">{formatNaira(totalPaid)}</span>
          </div>
          <div className="flex justify-between text-sm text-gray-500">
            <span>Remaining</span>
            <span className="font-semibold text-red-500">{formatNaira(remaining)}</span>
          </div>

          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Progress</span>
              <span>{paidPercent}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-green-500 transition-all duration-500"
                style={{ width: `${paidPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Payment history */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Payment history</h2>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-4">
            {payments.length === 0 ? (
              <EmptyState
                icon={Receipt}
                message="No payments logged yet."
              />
            ) : (
              payments.map((p) => (
                <PaymentItem
                  key={p.id}
                  payment={p}
                  isReceiver={isReceiver}
                  onConfirm={handleConfirm}
                  confirming={confirmingId === p.id}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Log payment button */}
      <div className="fixed bottom-0 left-0 right-0 flex justify-center bg-white border-t border-gray-100">
        <div className="w-full max-w-[640px] px-4 py-4">
          <button
            onClick={openLogSheet}
            className="w-full rounded-2xl bg-green-600 py-3.5 text-sm font-semibold text-white active:scale-[0.98] transition-transform"
          >
            Log New Payment
          </button>
        </div>
      </div>

      {/* Log payment bottom sheet */}
      <BottomSheet open={sheetOpen} onClose={() => setSheetOpen(false)} title="Log a Payment">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount (₦)
            </label>
            <input
              type="number"
              inputMode="decimal"
              value={logAmount}
              onChange={(e) => setLogAmount(e.target.value)}
              placeholder="0.00"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Note <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={logNote}
              onChange={(e) => setLogNote(e.target.value)}
              placeholder="e.g. First instalment"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          {logError && (
            <p className="text-sm text-red-500">{logError}</p>
          )}

          <button
            onClick={handleLogPayment}
            disabled={logging}
            className="w-full rounded-2xl bg-green-600 py-3.5 text-sm font-semibold text-white disabled:opacity-60 active:scale-[0.98] transition-transform"
          >
            {logging ? "Logging..." : "Confirm Payment"}
          </button>
        </div>
      </BottomSheet>
    </div>
  );
}
