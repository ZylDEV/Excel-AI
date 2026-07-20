import React, { createContext, useContext, useState, useCallback } from "react";

interface SidebarItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}

interface RightSidebarContextType {
  setItems: (items: SidebarItem[]) => void;
  items: SidebarItem[];
}

const RightSidebarContext = createContext<RightSidebarContextType | null>(null);

export const useRightSidebar = () => {
  const ctx = useContext(RightSidebarContext);
  if (!ctx) throw new Error("useRightSidebar must be used within RightSidebarProvider");
  return ctx;
};

export const RightSidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [items, setItems] = useState<SidebarItem[]>([]);

  return (
    <RightSidebarContext.Provider value={{ setItems, items }}>
      {children}
    </RightSidebarContext.Provider>
  );
};

export default RightSidebarContext;
