import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { getActiveSheetData } from "../services/api";

export interface SheetData {
  sheetName: string;
  headers: string[];
  data: unknown[][];
}

interface WorkbookState {
  activeSheet: SheetData | null;
  isLoading: boolean;
  error: string;
}

interface WorkbookContextType extends WorkbookState {
  refresh: () => Promise<void>;
}

const WorkbookContext = createContext<WorkbookContextType | null>(null);

export const useWorkbook = (): WorkbookContextType => {
  const ctx = useContext(WorkbookContext);
  if (!ctx) throw new Error("useWorkbook must be used within WorkbookProvider");
  return ctx;
};

export const WorkbookProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeSheet, setActiveSheet] = useState<SheetData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await getActiveSheetData();
      setActiveSheet(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal membaca Excel.";
      setError(msg);
      setActiveSheet(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <WorkbookContext.Provider value={{ activeSheet, isLoading, error, refresh }}>
      {children}
    </WorkbookContext.Provider>
  );
};

export default WorkbookContext;
