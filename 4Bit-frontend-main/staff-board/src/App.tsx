import React from 'react';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';

const AppContent: React.FC = () => {
  const { currentUser, isAuthenticated, isRestoring, logout } = useAuth();
  if (isRestoring) return <div className="min-h-screen grid place-items-center text-slate-600">Restoring session…</div>;
  if (!isAuthenticated) return <LoginPage onLoginSuccess={() => undefined} />;
  return <div className="min-h-screen bg-slate-50 text-slate-900">
    <nav className="border-b bg-white"><div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4"><div><div className="font-black text-emerald-950">4BIT VoiceCare</div><div className="text-sm text-slate-600">Department and hospital operations</div></div><div className="flex items-center gap-4 text-sm"><span>{currentUser?.name} · {currentUser?.role}</span><button onClick={logout} className="rounded-lg border px-3 py-2 font-semibold">Sign out</button></div></div></nav>
    <main className="px-4"><DashboardPage /></main>
  </div>;
};

export const App: React.FC = () => <AuthProvider><AppContent /></AuthProvider>;
export default App;
