import InstallPrompt from "@/components/InstallPrompt";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="w-full min-h-screen">
        {children}
      </div>
      <InstallPrompt />
    </>
  );
}
