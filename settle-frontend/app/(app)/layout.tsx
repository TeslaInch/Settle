import InstallPrompt from "@/components/InstallPrompt";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <InstallPrompt />
    </>
  );
}
