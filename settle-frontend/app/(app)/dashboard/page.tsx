"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Plus, TrendingDown, TrendingUp } from "lucide-react";

import { getAgreements, type Agreement } from "@/lib/api";
import { getFirstName, getGreeting } from "@/lib/utils";
import AgreementCard from "@/components/AgreementCard";
import EmptyState from "@/components/EmptyState";
import LoadingSpinner from "@/components/LoadingSpinner";

type Tab = "owe-me" | "i-owe";

export default function DashboardPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("owe-me");
  const [agreements, setAgreements] = useState<Agreement[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Read user from localStorage (set at login)
  const rawUser =
    typeof window !== "undefined" ? localStorage.getItem("settle_user") : null;
  const user = rawUser ? JSON.parse(rawUser) : null;
  const userId: string = user?.id ?? "";
  const greeting = getGreeting(getFirstName(user?.full_name));

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    const res = await getAgreements();
    if (res.error) {
      setError(res.error);
    } else {
      setAgreements(res.data ?? []);
    }

    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Pull-to-refresh via pointer events on mobile
  const handleRefresh = () => load(true);

  const owesMe = agreements.filter((a) => a.initiator_id === userId);
  const iOwe = agreements.filter(
    (a) => a.counterparty_id === userId || a.counterparty_phone === user?.phone_number
  );

  const current = tab === "owe-me" ? owesMe : iOwe;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white px-4 pt-12 md:pt-6 pb-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Settle</p>
            <h1 className="text-xl font-bold text-gray-900 mt-0.5">{greeting}</h1>
          </div>
          {refreshing && (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-green-600 border-t-transparent" />
          )}
        </div>

        {/* Tabs */}
        <div className="mt-4 flex gap-1 bg-gray-100 rounded-xl p-1">
          <button
            onClick={() => setTab("owe-me")}
            className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium transition-colors ${
              tab === "owe-me"
                ? "bg-white text-green-700 shadow-sm"
                : "text-gray-500"
            }`}
          >
            <TrendingUp size={15} />
            They Owe Me
          </button>
          <button
            onClick={() => setTab("i-owe")}
            className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium transition-colors ${
              tab === "i-owe"
                ? "bg-white text-red-600 shadow-sm"
                : "text-gray-500"
            }`}
          >
            <TrendingDown size={15} />
            I Owe
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4">
        {loading ? (
          <LoadingSpinner className="mt-20" />
        ) : error ? (
          <div className="mt-10 text-center">
            <p className="text-sm text-red-500">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-3 text-sm text-green-600 font-medium"
            >
              Try again
            </button>
          </div>
        ) : current.length === 0 ? (
          <EmptyState
            icon={FileText}
            message={
              tab === "owe-me"
                ? "No one owes you anything yet. Create an agreement to start tracking."
                : "You have no outstanding debts. Lucky you."
            }
            ctaLabel="Create your first agreement"
            onCta={() => router.push("/agreements/new")}
          />
        ) : (
          <div className="flex flex-col gap-3">
            {current.map((a) => (
              <AgreementCard key={a.id} agreement={a} currentUserId={userId} />
            ))}
          </div>
        )}
      </div>

      {/* FAB — positioned relative to app-shell, not viewport edge */}
      <div className="pointer-events-none fixed bottom-0 left-0 right-0 flex justify-center z-40">
        <div className="relative w-full max-w-[640px]">
          <button
            onClick={() => router.push("/agreements/new")}
            aria-label="Create new agreement"
            className="pointer-events-auto absolute bottom-6 right-4 flex h-14 w-14 items-center justify-center rounded-full bg-green-600 shadow-lg active:scale-95 transition-transform"
          >
            <Plus size={26} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
