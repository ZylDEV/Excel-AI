import React from "react";
import { RefreshCw, Database, AlertCircle } from "lucide-react";
import { useWorkbook } from "../contexts/WorkbookContext";

const DataBar: React.FC = () => {
  const { activeSheet, isLoading, error, refresh } = useWorkbook();

  if (error) {
    return (
      <div className="data-bar data-bar-error">
        <AlertCircle size={14} />
        <span className="data-bar-text">{error}</span>
        <button className="data-bar-btn" onClick={refresh} title="Coba lagi">
          <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="data-bar data-bar-loading">
        <div className="data-bar-spinner" />
        <span className="data-bar-text">Membaca data dari Excel...</span>
      </div>
    );
  }

  if (activeSheet) {
    return (
      <div className="data-bar data-bar-active">
        <Database size={14} />
        <span className="data-bar-text">
          {activeSheet.sheetName} — {activeSheet.data.length} baris &times; {activeSheet.headers.length} kolom
        </span>
        <button className="data-bar-btn" onClick={refresh} title="Refresh data dari Excel">
          <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  return null;
};

export default DataBar;
