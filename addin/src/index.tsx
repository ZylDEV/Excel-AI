import React, { useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";
import { WorkbookProvider } from "./contexts/WorkbookContext";
import Layout from "./components/Layout";
import { TabKey } from "./components/Navbar";
import DataBar from "./components/DataBar";
import AIPage from "./pages/AIPage";
import ExplainPage from "./pages/ExplainPage";
import CleanerPage from "./pages/CleanerPage";
import AuditPage from "./pages/AuditPage";
import SettingsPage from "./pages/SettingsPage";
import DashboardPage from "./pages/DashboardPage";
import ForecastPage from "./pages/ForecastPage";
import InsightPage from "./pages/InsightPage";
import FraudPage from "./pages/FraudPage";
import RiskPage from "./pages/RiskPage";
import FinancialPage from "./pages/FinancialPage";
import InventoryPage from "./pages/InventoryPage";
import SalesPage from "./pages/SalesPage";
import HRPage from "./pages/HRPage";
import ConnectorPage from "./pages/ConnectorPage";

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>("ai");

  const renderPage = () => {
    switch (activeTab) {
      case "ai":         return <AIPage />;
      case "explain":    return <ExplainPage />;
      case "cleaner":    return <CleanerPage />;
      case "audit":      return <AuditPage />;
      case "connector":  return <ConnectorPage />;
      case "dashboard":  return <DashboardPage />;
      case "forecast":   return <ForecastPage />;
      case "insights":   return <InsightPage />;
      case "fraud":      return <FraudPage />;
      case "risk":       return <RiskPage />;
      case "financial":  return <FinancialPage />;
      case "inventory":  return <InventoryPage />;
      case "sales":      return <SalesPage />;
      case "hr":         return <HRPage />;
      case "settings":   return <SettingsPage />;
      default:           return <AIPage />;
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      <DataBar />
      {renderPage()}
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <WorkbookProvider>
      <AppContent />
    </WorkbookProvider>
  );
};

const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);

  // Cek apakah di Excel add-in
  if (typeof Office !== "undefined" && typeof Office.onReady === "function") {
    // Di Excel — tunggu Office siap
    Office.onReady(() => {
      root.render(<App />);
    });
  } else {
    // Di browser — langsung render
    root.render(<App />);
  }
}
