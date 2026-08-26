import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-surface-dark">
      <Navbar />
      <Sidebar />
      <main className="pt-[56px] lg:pl-[240px] transition-all duration-300">
        {children}
      </main>
    </div>
  );
}
