"use client";

import { usePathname, useRouter } from "next/navigation";
import { Home, Plus, FileText } from "lucide-react";

export default function BottomNav() {
  const router = useRouter();
  const pathname = usePathname();

  const tabs = [
    {
      label: "Home",
      icon: Home,
      path: "/dashboard",
    },
    {
      label: "New",
      icon: Plus,
      path: "/agreements/new",
    },
    {
      label: "Agreements",
      icon: FileText,
      path: "/agreements",
    },
  ];

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50
                    bg-white border-t border-gray-100
                    flex justify-around items-center
                    px-4 py-2 pb-safe"
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = pathname === tab.path || pathname.startsWith(tab.path + "/");

        return (
          <button
            key={tab.path}
            onClick={() => router.push(tab.path)}
            className={`flex flex-col items-center gap-1 py-2 px-4 rounded-xl transition-colors ${
              isActive
                ? "text-[#1B4332]"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
            <span className="text-[11px] font-medium">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
