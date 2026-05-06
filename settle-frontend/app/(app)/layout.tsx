import InstallPrompt from "@/components/InstallPrompt";
import BottomNav from "@/components/BottomNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="w-full min-h-screen pb-20">
        {children}
      </div>
      <BottomNav />
      <InstallPrompt />
    </>
  );
}
