"use client";

import { useRouter } from "next/navigation";
import { type Agreement } from "@/lib/api";
import { formatNaira, getDaysRelative } from "@/lib/utils";
import StatusBadge from "./StatusBadge";

interface Props {
  agreement: Agreement;
  currentUserId: string;
}

export default function AgreementCard({ agreement, currentUserId }: Props) {
  const router = useRouter();
  const { label, overdue } = getDaysRelative(agreement.repayment_date);

  const otherParty =
    agreement.other_party_name ?? agreement.counterparty_phone;

  return (
    <button
      onClick={() => router.push(`/agreements/${agreement.id}`)}
      className="w-full text-left bg-white rounded-2xl shadow-sm border border-gray-100 p-4 active:scale-[0.98] transition-transform"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 truncate">{agreement.title}</p>
          <p className="text-sm text-gray-500 mt-0.5 truncate">{otherParty}</p>
        </div>
        <StatusBadge status={agreement.status} />
      </div>

      <div className="mt-3 flex items-end justify-between">
        <span className="text-2xl font-bold text-gray-900">
          {formatNaira(agreement.amount)}
        </span>
        <span
          className={
            overdue
              ? "text-sm font-medium text-red-600"
              : "text-sm text-gray-400"
          }
        >
          {label}
        </span>
      </div>
    </button>
  );
}
