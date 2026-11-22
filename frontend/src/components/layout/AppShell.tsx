import { Outlet } from "react-router-dom";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { NAV_ITEMS } from "@/routes/nav-items";

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-graphite-950">
      <Sidebar items={NAV_ITEMS} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}