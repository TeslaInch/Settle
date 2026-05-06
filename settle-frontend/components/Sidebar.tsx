"use client";

import { usePathname, useRouter } from "next/navigation";
import { Home, Plus, LogOut } from "lucide-react";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  const links = [
    { label: "Dashboard", icon: Home, path: "/dashboard" },
    { label: "New Agreement", icon: Plus, path: "/agreements/new" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("settle_token");
    localStorage.removeItem("settle_user");
    router.push("/login");
  };

  return (
    <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-white border-r border-gray-100 fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-6 py-6 border-b border-gray-100">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#1B4332" />
          <text
            x="16"
            y="22"
            textAnchor="middle"
            fill="white"
            fontSize="20"
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            S
          </text>
        </svg>
        <span className="text-xl font-bold text-[#1B4332]">Settle</span>
      </div>

      {/* Nav links */}
      <nav className="flex flex-col gap-1 px-3 py-4 flex-1">
        {links.map((link) => {
          const Icon = link.icon;
          const active =
            pathname === link.path ||
            (link.path !== "/dashboard" && pathname.startsWith(link.path));
          return (
            <button
              key={link.path}
              onClick={() => router.push(link.path)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors w-full text-left ${
                active
                  ? "bg-green-50 text-green-700"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              <Icon size={18} />
              {link.label}
            </button>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-gray-100">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors w-full"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
