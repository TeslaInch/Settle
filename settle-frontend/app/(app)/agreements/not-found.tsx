import Link from "next/link";

export default function AgreementNotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#9ca3af"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>
      <h1 className="text-lg font-bold text-gray-900 mb-2">Agreement not found</h1>
      <p className="text-sm text-gray-500 max-w-[260px] leading-relaxed">
        This agreement doesn&apos;t exist or you don&apos;t have access to it.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
