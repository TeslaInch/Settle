"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to console in dev; swap for a real error tracker in prod
    console.error("[Settle] Unhandled error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-red-50">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#dc2626"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h1 className="text-lg font-bold text-gray-900 mb-2">Something went wrong</h1>
      <p className="text-sm text-gray-500 max-w-[260px] leading-relaxed">
        An unexpected error occurred. Your data is safe — please try again.
      </p>
      <button
        onClick={reset}
        className="mt-6 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white active:scale-95 transition-transform"
      >
        Try again
      </button>
    </div>
  );
}
