import React, { useState } from "react";
import {
  Sparkles,
  Database,
  BarChart3,
  Shield,
  Settings,
  SearchCheck,
  Cable,
  LayoutDashboard,
  TrendingUp,
  Lightbulb,
  ShieldAlert,
  AlertTriangle,
  DollarSign,
  PackageSearch,
  Users,
} from "lucide-react";

export type GroupKey = "ai" | "data" | "intel" | "enterprise" | "settings";
export type TabKey = string;

interface SubItem {
  key: TabKey;
  label: string;
  icon: React.ReactNode;
}

interface Group {
  key: GroupKey;
  label: string;
  icon: React.ReactNode;
  items: SubItem[];
}

const GROUPS: Group[] = [
  {
    key: "ai", label: "AI", icon: <Sparkles size={18} />,
    items: [
      { key: "ai", label: "AI Assistant", icon: <Sparkles size={16} /> },
    ],
  },
  {
    key: "data", label: "Data", icon: <Database size={18} />,
    items: [
      { key: "cleaner", label: "Bersihkan", icon: <Sparkles size={16} /> },
      { key: "audit", label: "Audit", icon: <SearchCheck size={16} /> },
      { key: "connector", label: "Konektor", icon: <Cable size={16} /> },
    ],
  },
  {
    key: "intel", label: "Insights", icon: <BarChart3 size={18} />,
    items: [
      { key: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={16} /> },
      { key: "forecast", label: "Forecast", icon: <TrendingUp size={16} /> },
      { key: "insights", label: "Insight", icon: <Lightbulb size={16} /> },
    ],
  },
  {
    key: "enterprise", label: "Business", icon: <Shield size={18} />,
    items: [
      { key: "fraud", label: "Fraud", icon: <ShieldAlert size={16} /> },
      { key: "risk", label: "Risk", icon: <AlertTriangle size={16} /> },
      { key: "financial", label: "Keuangan", icon: <DollarSign size={16} /> },
      { key: "inventory", label: "Gudang", icon: <PackageSearch size={16} /> },
      { key: "sales", label: "Sales", icon: <TrendingUp size={16} /> },
      { key: "hr", label: "HR", icon: <Users size={16} /> },
    ],
  },
  {
    key: "settings", label: "Settings", icon: <Settings size={18} />,
    items: [
      { key: "settings", label: "Pengaturan", icon: <Settings size={16} /> },
    ],
  },
];

// Find which group a tab belongs to
function findGroup(tabKey: TabKey): Group {
  for (const g of GROUPS) {
    if (g.items.some((i) => i.key === tabKey)) return g;
  }
  return GROUPS[0];
}

interface Props {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

const Navbar: React.FC<Props> = ({ activeTab, onTabChange }) => {
  const activeGroup = findGroup(activeTab);

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo"><img src="/assets/logo.png" alt="EGA" /></span>
        <span className="navbar-title">Excel AI</span>
      </div>

      {/* Main group tabs */}
      <div className="navbar-groups">
        {GROUPS.map((g) => (
          <button
            key={g.key}
            className={`navbar-group ${activeGroup.key === g.key ? "active" : ""}`}
            onClick={() => onTabChange(g.items[0].key)}
            title={g.label}
          >
            <span className="navbar-group-icon">{g.icon}</span>
            <span className="navbar-group-label">{g.label}</span>
          </button>
        ))}
      </div>


    </nav>
  );
};

export { GROUPS, findGroup };
export default Navbar;
