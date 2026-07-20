import React, { useState } from "react";
import Navbar, { TabKey, GROUPS, findGroup } from "./Navbar";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { RightSidebarProvider, useRightSidebar } from "../contexts/RightSidebarContext";

interface Props {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  children: React.ReactNode;
}

const Sidebar: React.FC<{
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  collapsed: boolean;
  onToggle: () => void;
}> = ({ activeTab, onTabChange, collapsed, onToggle }) => {
  const group = findGroup(activeTab);

  return (
    <aside className={`sidebar sidebar-left ${collapsed ? "sidebar-collapsed" : "sidebar-expanded"}`}>
      <button className="sidebar-toggle" onClick={onToggle} title={collapsed ? "Perluas" : "Ciutkan"}>
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      <div className="sidebar-items">
        {group.items.map((item) => (
          <button
            key={item.key}
            className={`sidebar-item ${activeTab === item.key ? "active" : ""}`}
            onClick={() => onTabChange(item.key)}
            title={item.label}
          >
            <span className="sidebar-item-icon">{item.icon}</span>
            {!collapsed && <span className="sidebar-item-label">{item.label}</span>}
          </button>
        ))}
      </div>
    </aside>
  );
};

const RightSidebar: React.FC = () => {
  const { items } = useRightSidebar();
  const [collapsed, setCollapsed] = useState(true);
  if (items.length === 0) return null;

  return (
    <aside className={`sidebar sidebar-right ${collapsed ? "sidebar-rcollapsed" : "sidebar-rexpanded"}`}>
      <button className="sidebar-toggle" onClick={() => setCollapsed(!collapsed)} title={collapsed ? "Perluas" : "Ciutkan"}>
        {collapsed ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>

      <div className="sidebar-items">
        {items.map((item) => (
          <button
            key={item.key}
            className={`sidebar-item ${item.active ? "active" : ""}`}
            onClick={item.onClick}
            title={item.label}
          >
            <span className="sidebar-item-icon">{item.icon}</span>
            {!collapsed && <span className="sidebar-item-label">{item.label}</span>}
          </button>
        ))}
      </div>
    </aside>
  );
};

const LayoutInner: React.FC<Props> = ({ activeTab, onTabChange, children }) => {
  const group = findGroup(activeTab);
  const showSidebar = group.items.length > 1 && activeTab !== "settings";
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  return (
    <div className="app-layout">
      <Navbar activeTab={activeTab} onTabChange={onTabChange} />
      <div className="app-body">
        {showSidebar && (
          <Sidebar
            activeTab={activeTab}
            onTabChange={onTabChange}
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        )}
        <main className="app-content">{children}</main>
        <RightSidebar />
      </div>
    </div>
  );
};

const Layout: React.FC<Props> = (props) => {
  return (
    <RightSidebarProvider>
      <LayoutInner {...props} />
    </RightSidebarProvider>
  );
};

export default Layout;
