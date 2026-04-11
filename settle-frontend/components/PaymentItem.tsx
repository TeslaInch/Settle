"use client";

import { type Payment } from "@/lib/api";
import { formatNaira, formatDate } from "@/lib/utils";
import { CheckCircle, Clock } from "lucide-react";

interface Props {
  payment: Payment;
  isReceiver: boolean;
  onConfirm?: (paymentId: string) => void;
  confirming?: boolean;
}

export default function PaymentItem({
  payment,
  isReceiver,
  onConfirm,
  confirming,
}: Props) {
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
        {payment.confirmed_by_receiver ? (
          <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
            <CheckCircle size={13} />
            Confirmed
          </span>
        ) : isReceiver && onConfirm ? (
          <button
            onClick={() => onConfirm(payment.id)}
            disabled={confirming}
            className="text-xs bg-green-600 text-white rounded-full px-3 py-1 font-medium disabled:opacity-50"
          >
            {confirming ? "..." : "Confirm Receipt"}
          </button>
        ) : (
          <span className="flex items-center gap-1 text-xs text-yellow-600 font-medium">
            <Clock size={13} />
            Pending
          </span>
        )}
      </div>
    </div>
  );
}
