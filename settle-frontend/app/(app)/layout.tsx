import InstallPrompt from "@/components/InstallPrompt";
import BottomNav from "@/components/BottomNav";
import Sidebar from "@/components/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop sidebar */}
      <Sidebar />

      {/* Main content — offset by sidebar on desktop */}
      <div className="lg:ml-64 pb-16 lg:pb-0">
        {children}
      </div>

      {/* Mobile bottom nav only */}
      <div className="lg:hidden">
        <BottomNav />
      </div>

      <InstallPrompt />
    </div>
  );
}
