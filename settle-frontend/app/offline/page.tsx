export default function OfflinePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6 text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-50">
        {/* Wifi-off icon drawn inline — no import needed */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="36"
          height="36"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#16a34a"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <line x1="1" y1="1" x2="23" y2="23" />
          <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
          <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
          <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
          <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <circle cx="12" cy="20" r="1" fill="#16a34a" stroke="none" />
        </svg>
      </div>

      <h1 className="text-xl font-bold text-gray-900 mb-2">You&apos;re offline</h1>
      <p className="text-sm text-gray-500 leading-relaxed max-w-[260px]">
        Your saved agreements are still viewable. Connect to the internet to sync changes.
      </p>

      <button
        onClick={() => window.location.reload()}
        className="mt-8 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white active:scale-95 transition-transform"
      >
        Try again
      </button>
    </div>
  );
}
