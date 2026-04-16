import Link from "next/link";

// ── Phone mockup SVG ──────────────────────────────────────────────────────────
function PhoneMockup() {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        marginTop: 40,
        marginBottom: 8,
      }}
    >
      <svg
        width="180"
        height="320"
        viewBox="0 0 180 320"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Phone body */}
        <rect x="4" y="4" width="172" height="312" rx="24" fill="#1B4332" />
        <rect x="8" y="8" width="164" height="304" rx="21" fill="#F9FAFB" />

        {/* Status bar notch */}
        <rect x="60" y="14" width="60" height="10" rx="5" fill="#D1D5DB" />

        {/* App header bar */}
        <rect x="8" y="32" width="164" height="36" fill="#1B4332" />
        <text x="24" y="55" fontFamily="system-ui" fontSize="13" fontWeight="700" fill="white">
          Settle
        </text>
        <circle cx="148" cy="50" r="10" fill="#2D6A4F" />
        <text x="144" y="54" fontFamily="system-ui" fontSize="10" fill="white">✓</text>

        {/* Agreement card */}
        <rect x="16" y="80" width="148" height="90" rx="10" fill="white"
          style={{ filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.08))" }} />
        {/* Card title */}
        <text x="28" y="100" fontFamily="system-ui" fontSize="10" fontWeight="600" fill="#111827">
          Rent Loan — Emeka
        </text>
        {/* Amount */}
        <text x="28" y="120" fontFamily="system-ui" fontSize="18" fontWeight="700" fill="#1B4332">
          ₦150,000
        </text>
        {/* Status badge */}
        <rect x="28" y="130" width="44" height="16" rx="8" fill="#D1FAE5" />
        <text x="36" y="142" fontFamily="system-ui" fontSize="8" fontWeight="600" fill="#065F46">
          Active
        </text>
        {/* Due date */}
        <text x="28" y="162" fontFamily="system-ui" fontSize="9" fill="#6B7280">
          Due: 30 Jun 2025 · 14 days left
        </text>

        {/* Seal badge */}
        <rect x="16" y="184" width="148" height="52" rx="10" fill="#ECFDF5"
          style={{ filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.06))" }} />
        <text x="28" y="204" fontFamily="system-ui" fontSize="9" fontWeight="600" fill="#065F46">
          🔒  Agreement Sealed
        </text>
        <text x="28" y="218" fontFamily="system-ui" fontSize="8" fill="#6B7280">
          Both parties confirmed · 12 May 2025
        </text>
        <text x="28" y="230" fontFamily="system-ui" fontSize="7" fill="#9CA3AF">
          Hash: a3f9c2…d84e
        </text>

        {/* Bottom nav bar */}
        <rect x="8" y="280" width="164" height="32" rx="0" fill="#F3F4F6" />
        <rect x="8" y="280" width="164" height="32" rx="0"
          style={{ borderBottomLeftRadius: 21, borderBottomRightRadius: 21 }} fill="#F3F4F6" />
        <text x="36" y="300" fontFamily="system-ui" fontSize="9" fill="#6B7280">Home</text>
        <text x="82" y="300" fontFamily="system-ui" fontSize="9" fill="#1B4332" fontWeight="600">Agreements</text>
        <text x="132" y="300" fontFamily="system-ui" fontSize="9" fill="#6B7280">Profile</text>

        {/* Home indicator */}
        <rect x="70" y="308" width="40" height="4" rx="2" fill="#D1D5DB" />
      </svg>
    </div>
  );
}

// ── Step card ─────────────────────────────────────────────────────────────────
function Step({
  number,
  title,
  body,
}: {
  number: string;
  title: string;
  body: string;
}) {
  return (
    <div style={styles.stepCard}>
      <div style={styles.stepNumber}>{number}</div>
      <div>
        <p style={styles.stepTitle}>{title}</p>
        <p style={styles.stepBody}>{body}</p>
      </div>
    </div>
  );
}

// ── Use-case card ─────────────────────────────────────────────────────────────
function UseCard({ emoji, text }: { emoji: string; text: string }) {
  return (
    <div style={styles.useCard}>
      <span style={styles.useEmoji}>{emoji}</span>
      <p style={styles.useText}>{text}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div style={styles.page}>
      {/* ── Nav ── */}
      <nav style={styles.nav}>
        <div style={styles.navLogo}>
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#1B4332" />
            <path
              d="M10 22l6-12 6 12"
              stroke="#fff"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path d="M12.5 18h7" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
          <span style={styles.navWordmark}>Settle</span>
        </div>
        <Link href="/login" style={styles.navSignIn}>
          Sign In
        </Link>
      </nav>

      {/* ── Hero ── */}
      <section style={styles.hero}>
        <PhoneMockup />
        <h1 style={styles.heroHeadline}>
          Never lose money or a friendship over a handshake again.
        </h1>
        <p style={styles.heroSub}>
          Settle witnesses your informal agreements. Both parties confirm.
          The record is sealed forever.
        </p>
        <Link href="/login" style={styles.heroCta}>
          Create Your First Agreement — It&apos;s Free
        </Link>
      </section>

      {/* ── How It Works ── */}
      <section style={styles.section}>
        <p style={styles.sectionLabel}>How it works</p>
        <h2 style={styles.sectionTitle}>Three steps. Done.</h2>

        <div style={styles.stepsWrap}>
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
      <section style={{ ...styles.section, backgroundColor: "#F9FAFB" }}>
        <p style={styles.sectionLabel}>Who it&apos;s for</p>
        <h2 style={styles.sectionTitle}>Built for everyday Nigerians</h2>

        <div style={styles.useGrid}>
          <UseCard emoji="🤝" text="Lending money to a friend or family" />
          <UseCard emoji="🛒" text="Trader giving goods on credit" />
          <UseCard emoji="🏠" text="Collecting rent in installments" />
          <UseCard emoji="📋" text="Any agreement you need witnessed" />
        </div>
      </section>

      {/* ── Trust ── */}
      <section style={styles.trustSection}>
        <div style={styles.trustIcon} aria-hidden="true">🔒</div>
        <h2 style={styles.trustTitle}>Your record can never be changed</h2>
        <p style={styles.trustBody}>
          The moment both parties confirm, Settle seals the agreement with a
          unique fingerprint. Any attempt to alter it is detectable. Your
          WhatsApp receipt is your proof.
        </p>

        {/* Fingerprint visual */}
        <div style={styles.hashBox}>
          <p style={styles.hashLabel}>Agreement fingerprint</p>
          <p style={styles.hashValue}>a3f9c2b1…8d4e7f02</p>
          <p style={styles.hashSub}>Generated at confirmation · Cannot be forged</p>
        </div>
      </section>

      {/* ── CTA repeat ── */}
      <section style={styles.ctaSection}>
        <h2 style={styles.ctaTitle}>Start for free.</h2>
        <p style={styles.ctaSub}>No bank account needed.</p>
        <Link href="/login" style={styles.ctaButton}>
          Get Started
        </Link>
      </section>

      {/* ── Footer ── */}
      <footer style={styles.footer}>
        <p style={styles.footerText}>Settle — Built for Nigeria</p>
      </footer>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  page: {
    backgroundColor: "#FFFFFF",
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    color: "#111827",
    maxWidth: 480,
    margin: "0 auto",
    overflowX: "hidden",
  },

  // Nav
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px 20px",
    borderBottom: "1px solid #F3F4F6",
    position: "sticky",
    top: 0,
    backgroundColor: "#FFFFFF",
    zIndex: 10,
  },
  navLogo: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  navWordmark: {
    fontSize: 18,
    fontWeight: 700,
    color: "#1B4332",
    letterSpacing: "-0.4px",
  },
  navSignIn: {
    fontSize: 14,
    fontWeight: 600,
    color: "#1B4332",
    border: "1.5px solid #1B4332",
    borderRadius: 20,
    padding: "6px 16px",
    textDecoration: "none",
  },

  // Hero
  hero: {
    padding: "32px 24px 48px",
    textAlign: "center",
    backgroundColor: "#FFFFFF",
  },
  heroHeadline: {
    fontSize: 28,
    fontWeight: 800,
    lineHeight: 1.25,
    letterSpacing: "-0.6px",
    color: "#111827",
    margin: "0 0 16px",
  },
  heroSub: {
    fontSize: 16,
    lineHeight: 1.6,
    color: "#6B7280",
    margin: "0 0 28px",
  },
  heroCta: {
    display: "inline-block",
    backgroundColor: "#1B4332",
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: 700,
    padding: "14px 24px",
    borderRadius: 14,
    textDecoration: "none",
    lineHeight: 1.3,
  },

  // Sections
  section: {
    padding: "48px 24px",
    backgroundColor: "#FFFFFF",
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#1B4332",
    margin: "0 0 8px",
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 800,
    letterSpacing: "-0.4px",
    color: "#111827",
    margin: "0 0 28px",
  },

  // Steps
  stepsWrap: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  stepCard: {
    display: "flex",
    alignItems: "flex-start",
    gap: 16,
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    padding: "16px 18px",
  },
  stepNumber: {
    flexShrink: 0,
    width: 32,
    height: 32,
    borderRadius: "50%",
    backgroundColor: "#1B4332",
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: "#111827",
    margin: "0 0 4px",
  },
  stepBody: {
    fontSize: 14,
    color: "#6B7280",
    lineHeight: 1.5,
    margin: 0,
  },

  // Use cases
  useGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 12,
  },
  useCard: {
    backgroundColor: "#FFFFFF",
    border: "1.5px solid #E5E7EB",
    borderRadius: 14,
    padding: "16px 14px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  useEmoji: {
    fontSize: 24,
  },
  useText: {
    fontSize: 13,
    fontWeight: 500,
    color: "#374151",
    lineHeight: 1.4,
    margin: 0,
  },

  // Trust
  trustSection: {
    padding: "48px 24px",
    backgroundColor: "#1B4332",
    textAlign: "center",
  },
  trustIcon: {
    fontSize: 36,
    marginBottom: 16,
  },
  trustTitle: {
    fontSize: 22,
    fontWeight: 800,
    color: "#FFFFFF",
    letterSpacing: "-0.4px",
    margin: "0 0 16px",
  },
  trustBody: {
    fontSize: 15,
    color: "#A7F3D0",
    lineHeight: 1.7,
    margin: "0 0 28px",
  },
  hashBox: {
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 12,
    padding: "16px 20px",
    textAlign: "left",
  },
  hashLabel: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    color: "#6EE7B7",
    margin: "0 0 6px",
  },
  hashValue: {
    fontSize: 16,
    fontWeight: 700,
    fontFamily: "monospace",
    color: "#FFFFFF",
    margin: "0 0 4px",
    letterSpacing: "0.04em",
  },
  hashSub: {
    fontSize: 12,
    color: "#A7F3D0",
    margin: 0,
  },

  // CTA repeat
  ctaSection: {
    padding: "56px 24px",
    textAlign: "center",
    backgroundColor: "#F9FAFB",
  },
  ctaTitle: {
    fontSize: 26,
    fontWeight: 800,
    color: "#111827",
    letterSpacing: "-0.5px",
    margin: "0 0 6px",
  },
  ctaSub: {
    fontSize: 15,
    color: "#6B7280",
    margin: "0 0 28px",
  },
  ctaButton: {
    display: "inline-block",
    backgroundColor: "#1B4332",
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: 700,
    padding: "15px 36px",
    borderRadius: 14,
    textDecoration: "none",
  },

  // Footer
  footer: {
    padding: "20px 24px",
    borderTop: "1px solid #F3F4F6",
    textAlign: "center",
  },
  footerText: {
    fontSize: 13,
    color: "#9CA3AF",
    margin: 0,
  },
};
