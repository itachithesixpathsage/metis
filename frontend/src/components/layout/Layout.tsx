import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '../../utils/cn';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="page-container flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && <div className="sidebar-overlay lg:hidden" onClick={() => setSidebarOpen(false)} aria-hidden="true" />}

      {/* Sidebar */}
      <Sidebar
        className={cn(sidebarOpen ? '' : 'sidebar-collapsed')}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <div className="main-shell flex min-h-screen flex-col">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
