import Link from "next/link";

// ── Phone mockup SVG ──────────────────────────────────────────────────────────
function PhoneMockup() {
  return (
    <div className="flex justify-center mt-8 mb-2 md:mt-0">
      <svg
        width="180"
        height="320"
        viewBox="0 0 180 320"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="w-[160px] h-auto md:w-[180px]"
      >
        <rect x="4" y="4" width="172" height="312" rx="24" fill="#1B4332" />
        <rect x="8" y="8" width="164" height="304" rx="21" fill="#F9FAFB" />
        <rect x="60" y="14" width="60" height="10" rx="5" fill="#D1D5DB" />
        <rect x="8" y="32" width="164" height="36" fill="#1B4332" />
        <text x="24" y="55" fontFamily="system-ui" fontSize="13" fontWeight="700" fill="white">Settle</text>
        <circle cx="148" cy="50" r="10" fill="#2D6A4F" />
        <text x="144" y="54" fontFamily="system-ui" fontSize="10" fill="white">✓</text>
        <rect x="16" y="80" width="148" height="90" rx="10" fill="white" />
        <text x="28" y="100" fontFamily="system-ui" fontSize="10" fontWeight="600" fill="#111827">Rent Loan — Emeka</text>
        <text x="28" y="120" fontFamily="system-ui" fontSize="18" fontWeight="700" fill="#1B4332">₦150,000</text>
        <rect x="28" y="130" width="44" height="16" rx="8" fill="#D1FAE5" />
        <text x="36" y="142" fontFamily="system-ui" fontSize="8" fontWeight="600" fill="#065F46">Active</text>
        <text x="28" y="162" fontFamily="system-ui" fontSize="9" fill="#6B7280">Due: 30 Jun 2025 · 14 days left</text>
        <rect x="16" y="184" width="148" height="52" rx="10" fill="#ECFDF5" />
        <text x="28" y="204" fontFamily="system-ui" fontSize="9" fontWeight="600" fill="#065F46">🔒  Agreement Sealed</text>
        <text x="28" y="218" fontFamily="system-ui" fontSize="8" fill="#6B7280">Both parties confirmed · 12 May 2025</text>
        <text x="28" y="230" fontFamily="system-ui" fontSize="7" fill="#9CA3AF">Hash: a3f9c2…d84e</text>
        <rect x="8" y="280" width="164" height="32" fill="#F3F4F6" />
        <text x="36" y="300" fontFamily="system-ui" fontSize="9" fill="#6B7280">Home</text>
        <text x="82" y="300" fontFamily="system-ui" fontSize="9" fill="#1B4332" fontWeight="600">Agreements</text>
        <text x="132" y="300" fontFamily="system-ui" fontSize="9" fill="#6B7280">Profile</text>
        <rect x="70" y="308" width="40" height="4" rx="2" fill="#D1D5DB" />
      </svg>
    </div>
  );
}

function Step({ number, title, body }: { number: string; title: string; body: string }) {
  return (
    <div className="flex items-start gap-4 bg-gray-50 rounded-2xl p-4">
      <div className="shrink-0 w-8 h-8 rounded-full bg-[#1B4332] text-white text-sm font-bold flex items-center justify-center">
        {number}
      </div>
      <div>
        <p className="text-sm font-bold text-gray-900 mb-1">{title}</p>
        <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
      </div>
    </div>
  );
}

function UseCard({ emoji, text }: { emoji: string; text: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 flex flex-col gap-2">
      <span className="text-2xl">{emoji}</span>
      <p className="text-sm font-medium text-gray-700 leading-snug">{text}</p>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="bg-white text-gray-900 font-sans overflow-x-hidden">

      {/* ── Nav ── */}
      <nav className="sticky top-0 z-10 bg-white border-b border-gray-100 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path d="M10 22l6-12 6 12" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span className="text-lg font-bold text-[#1B4332] tracking-tight">Settle</span>
        </div>
        <Link
          href="/login"
          className="text-sm font-semibold text-[#1B4332] border border-[#1B4332] rounded-full px-4 py-1.5 hover:bg-[#1B4332] hover:text-white transition-colors"
        >
          Sign In
        </Link>
      </nav>

      {/* ── Hero ── */}
      <section className="px-5 pt-10 pb-14 md:pt-16 md:pb-20 max-w-5xl mx-auto">
        <div className="md:grid md:grid-cols-2 md:gap-12 md:items-center">
          {/* Text */}
          <div className="text-center md:text-left">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold leading-tight tracking-tight text-gray-900 mb-4">
              Never lose money or a friendship over a handshake again.
            </h1>
            <p className="text-base sm:text-lg text-gray-500 leading-relaxed mb-8 max-w-md mx-auto md:mx-0">
              Settle witnesses your informal agreements. Both parties confirm.
              The record is sealed forever.
            </p>
            <Link
              href="/login"
              className="inline-block bg-[#1B4332] text-white text-base font-bold px-6 py-4 rounded-2xl leading-tight hover:bg-[#14532d] transition-colors"
            >
              Create Your First Agreement — It&apos;s Free
            </Link>
          </div>
          {/* Mockup */}
          <PhoneMockup />
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="px-5 py-14 bg-white max-w-5xl mx-auto">
        <p className="text-xs font-semibold uppercase tracking-widest text-[#1B4332] mb-2">How it works</p>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900 mb-8">Three steps. Done.</h2>
        <div className="flex flex-col gap-4 md:grid md:grid-cols-3">
          <Step
            number="1"
            title="You describe the agreement"
            body="Enter the amount, terms, and repayment date. Takes under a minute."
          />
          <Step
            number="2"
            title="The other person confirms"
            body="They get a WhatsApp link. They tap agree. No app download needed."
          />
          <Step
            number="3"
            title="It's sealed forever"
            body="Both parties get a permanent timestamped record on WhatsApp. Immutable."
          />
        </div>
      </section>

      {/* ── Who It's For ── */}
      <section className="px-5 py-14 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <p className="text-xs font-semibold uppercase tracking-widest text-[#1B4332] mb-2">Who it&apos;s for</p>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-gray-900 mb-8">
            Built for everyday Nigerians
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <UseCard emoji="🤝" text="Lending money to a friend or family" />
            <UseCard emoji="🛒" text="Trader giving goods on credit" />
            <UseCard emoji="🏠" text="Collecting rent in installments" />
            <UseCard emoji="📋" text="Any agreement you need witnessed" />
          </div>
        </div>
      </section>

      {/* ── Trust ── */}
      <section className="px-5 py-14 bg-[#1B4332] text-center">
        <div className="max-w-2xl mx-auto">
          <div className="text-4xl mb-4" aria-hidden="true">🔒</div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-4">
            Your record can never be changed
          </h2>
          <p className="text-base text-emerald-200 leading-relaxed mb-8">
            The moment both parties confirm, Settle seals the agreement with a
            unique fingerprint. Any attempt to alter it is detectable. Your
            WhatsApp receipt is your proof.
          </p>
          <div className="bg-white/10 rounded-2xl p-5 text-left">
            <p className="text-xs font-semibold uppercase tracking-widest text-emerald-300 mb-2">
              Agreement fingerprint
            </p>
            <p className="text-lg font-bold font-mono text-white tracking-wider mb-1">
              a3f9c2b1…8d4e7f02
            </p>
            <p className="text-xs text-emerald-300">Generated at confirmation · Cannot be forged</p>
          </div>
        </div>
      </section>

      {/* ── CTA repeat ── */}
      <section className="px-5 py-16 bg-gray-50 text-center">
        <div className="max-w-md mx-auto">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight mb-2">
            Start for free.
          </h2>
          <p className="text-base text-gray-500 mb-8">No bank account needed.</p>
          <Link
            href="/login"
            className="inline-block bg-[#1B4332] text-white text-base font-bold px-10 py-4 rounded-2xl hover:bg-[#14532d] transition-colors"
          >
            Get Started
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="px-5 py-5 border-t border-gray-100 text-center">
        <p className="text-sm text-gray-400">Settle — Built for Nigeria</p>
      </footer>

    </div>
  );
}
