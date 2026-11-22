import {
  AlertTriangle,
  FileSearch,
  FolderKanban,
  LayoutDashboard,
  SearchCode,
  Server,
  Settings,
} from "lucide-react";

import type { NavItem } from "@/types/navigation";

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", path: "/", icon: LayoutDashboard },
  { label: "Projects", path: "/projects", icon: FolderKanban },
  { label: "Log Explorer", path: "/logs", icon: FileSearch },
  { label: "Anomalies", path: "/incidents", icon: AlertTriangle },
  { label: "Services", path: "/services", icon: Server, disabled: true },
  {
    label: "Investigations",
    path: "/investigations",
    icon: SearchCode,
  },
  { label: "Settings", path: "/settings", icon: Settings, disabled: true },
];