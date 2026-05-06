"use client";

import { useState } from "react";
import { type Payment } from "@/lib/api";
import { formatNaira, formatDate } from "@/lib/utils";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";

interface Props {
  payment: Payment;
  isReceiver: boolean;
  onConfirm?: (paymentId: string) => void;
  onDispute?: (paymentId: string, reason: string) => void;
  confirming?: boolean;
  disputing?: boolean;
}

export default function PaymentItem({
  payment,
  isReceiver,
  onConfirm,
  onDispute,
  confirming,
  disputing,
}: Props) {
  const [showDisputeForm, setShowDisputeForm] = useState(false);
  const [disputeReason, setDisputeReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);

  const handleSubmitDispute = () => {
    if (disputeReason.trim().length < 10) {
      setReasonError("Reason must be at least 10 characters");
      return;
    }
    setReasonError(null);
    onDispute?.(payment.id, disputeReason.trim());
  };

  const handleCancelDispute = () => {
    setShowDisputeForm(false);
    setDisputeReason("");
    setReasonError(null);
  };

  // Show disputed badge
  if (payment.disputed) {
    return (
      <div className="flex items-start justify-between gap-3 py-3 border-b border-gray-100 last:border-0">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900">{formatNaira(payment.amount)}</p>
          {payment.note && (
            <p className="text-sm text-gray-500 mt-0.5 truncate">{payment.note}</p>
          )}
          <p className="text-xs text-gray-400 mt-1">{formatDate(payment.logged_at)}</p>
          {payment.dispute_reason && (
            <p className="text-xs text-gray-500 mt-1 italic">
              Dispute: {payment.dispute_reason}
            </p>
          )}
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="flex items-center gap-1 text-xs text-red-600 font-medium">
            <AlertCircle size={13} />
            Disputed
          </span>
        </div>
      </div>
    );
  }

  // Show confirmed badge
  if (payment.confirmed_by_receiver) {
    return (
      <div className="flex items-start justify-between gap-3 py-3 border-b border-gray-100 last:border-0">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900">{formatNaira(payment.amount)}</p>
          {payment.note && (
            <p className="text-sm text-gray-500 mt-0.5 truncate">{payment.note}</p>
          )}
          <p className="text-xs text-gray-400 mt-1">{formatDate(payment.logged_at)}</p>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
            <CheckCircle size={13} />
            Confirmed
          </span>
        </div>
      </div>
    );
  }

  // Show confirm and dispute buttons for receiver
  if (isReceiver && onConfirm) {
    return (
      <div className="py-3 border-b border-gray-100 last:border-0">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900">{formatNaira(payment.amount)}</p>
            {payment.note && (
              <p className="text-sm text-gray-500 mt-0.5 truncate">{payment.note}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">{formatDate(payment.logged_at)}</p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {showDisputeForm ? null : (
              <>
                <button
                  onClick={() => onConfirm(payment.id)}
                  disabled={confirming || disputing}
                  className="text-xs bg-green-600 text-white rounded-full px-3 py-1 font-medium disabled:opacity-50"
                >
                  {confirming ? "..." : "Confirm Receipt"}
                </button>
                {onDispute && (
                  <button
                    onClick={() => setShowDisputeForm(true)}
                    disabled={confirming || disputing}
                    className="text-xs bg-red-600 text-white rounded-full px-3 py-1 font-medium disabled:opacity-50"
                  >
                    Dispute
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Dispute form */}
        {showDisputeForm && (
          <div className="mt-3 bg-gray-50 rounded-xl p-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason for dispute
            </label>
            <textarea
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="Explain why you are disputing this payment..."
              rows={3}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
            />
            {reasonError && (
              <p className="text-xs text-red-500 mt-1">{reasonError}</p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleSubmitDispute}
                disabled={disputing}
                className="text-xs bg-red-600 text-white rounded-full px-4 py-1.5 font-medium disabled:opacity-50"
              >
                {disputing ? "Submitting..." : "Submit Dispute"}
              </button>
              <button
                onClick={handleCancelDispute}
                disabled={disputing}
                className="text-xs text-gray-500 font-medium px-2 py-1.5 hover:text-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Show pending badge for others
  return (
    <div className="flex items-start justify-between gap-3 py-3 border-b border-gray-100 last:border-0">
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900">{formatNaira(payment.amount)}</p>
        {payment.note && (
          <p className="text-sm text-gray-500 mt-0.5 truncate">{payment.note}</p>
        )}
        <p className="text-xs text-gray-400 mt-1">{formatDate(payment.logged_at)}</p>
      </div>

      <div className="flex flex-col items-end gap-1 shrink-0">
        <span className="flex items-center gap-1 text-xs text-yellow-600 font-medium">
          <Clock size={13} />
          Pending
        </span>
      </div>
    </div>
  );
}
