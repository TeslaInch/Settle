import InstallPrompt from "@/components/InstallPrompt";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* Centered shell — max 640px on large screens, full-width on mobile */}
      <div className="app-shell min-h-screen">
        {children}
      </div>
      <InstallPrompt />
    </>
  );
}
