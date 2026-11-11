import React from 'react';
import {
  HeartPulse,
  Building2,
  Users,
  Shield,
  LogOut,
} from 'lucide-react';
import { StaffRole } from '../../types/complaint';
import { cn } from '../../utils/cn';
import { useAuth } from '../../context/AuthContext';

export type ActiveTab = 'tasks' | 'overview' | 'escalations' | 'reviews' | 'grievances' | 'workload';

export interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  selectedUnit?: string;
  overdueCount: number;
  myTasksCount: number;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  selectedUnit,
  overdueCount: _overdueCount,
  onLogout,
}) => {
  const { currentUser, logout } = useAuth();
  const currentRole: StaffRole = currentUser?.role || 'Department Head';

  const handleLogoutClick = () => {
    logout();
    if (onLogout) onLogout();
  };

  const displayUnit =
    currentRole === 'Hospital Administrator' || currentRole === 'Higher Authority'
      ? 'All Hospital Departments'
      : selectedUnit || currentUser?.department || 'Sanitation & Maintenance';

  // RBAC Navigation Links tailored per role
  const getNavLinks = (): Array<{ id: ActiveTab; label: string; icon: React.ElementType; badge: number | null; badgeColor: string }> => {
    if (currentRole === 'Department Head' || currentRole === 'Hospital Administrator') {
      // Per Task 1: Completely delete the toggle buttons from this top header for Department Head and Hospital Administrator.
      // The header strictly contains only the hospital branding on the left and the user profile/sign-out button on the right.
      return [];
    }

    return [];
  };

  const navLinks = getNavLinks();

  const getRoleIcon = (role: StaffRole) => {
    switch (role) {
      case 'Department Head':
        return Users;
      case 'Hospital Administrator':
      case 'Higher Authority':
        return Shield;
    }
  };

  const RoleIcon = getRoleIcon(currentRole);

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-emerald-900 text-stone-50 border-b border-emerald-950/80 shadow-sm">
      {/* Top Context Strip */}
      <div className="bg-emerald-950 text-emerald-200/80 text-xs px-3 sm:px-4 py-1.5 flex items-center justify-between font-medium border-b border-emerald-900/40">
        <div className="flex items-center gap-2 truncate">
          <span className="flex h-2 w-2 relative shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
          </span>
          <span className="font-bold text-stone-100 text-[11px] sm:text-xs truncate">
            Hospital &bull; Staff Operations Hub
          </span>
          <span className="hidden md:inline text-emerald-300/80">&bull; Live Telemetry &amp; Proof Gate</span>
        </div>
        <div className="flex items-center gap-2.5 text-emerald-200/90 shrink-0 text-[11px]">
          <span className="hidden sm:inline font-medium text-stone-200">
            Operational Unit: {displayUnit}
          </span>
          <span className="bg-emerald-900/90 px-2 py-0.5 rounded font-mono text-emerald-100 border border-emerald-800 text-[10px]">
            GPS Geofence: Active
          </span>
        </div>
      </div>

      {/* Main App Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16 md:h-18 gap-3">
          {/* Hospital Branding */}
          <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
            <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-xl bg-emerald-800 text-amber-300 flex items-center justify-center shadow-xs border border-emerald-700/80 shrink-0">
              <HeartPulse className="w-5 h-5 sm:w-6 sm:h-6" aria-hidden="true" />
            </div>

            <div className="flex flex-col justify-center">
              <div className="flex items-center gap-2 whitespace-nowrap shrink-0">
                <span className="text-lg sm:text-xl md:text-2xl font-black tracking-tight text-stone-50 leading-none flex items-center">
                  4BIT&nbsp;<span className="text-amber-300 font-extrabold">VoiceCare</span>
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold bg-emerald-800 text-amber-200 border border-emerald-700 shadow-2xs leading-none shrink-0 self-center">
                  Staff Board
                </span>
              </div>
              <p className="text-[11px] text-emerald-200/80 font-medium hidden sm:flex items-center gap-1 mt-0.5 leading-tight">
                <Building2 className="w-3 h-3 text-emerald-300/70 shrink-0" />
                <span className="truncate">Hospital &bull; Resolution Management</span>
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links (Only rendered for roles that have top nav links, omitted for Department Head & Hospital Administrator) */}
          {navLinks.length > 0 && (
            <nav
              aria-label="Desktop Navigation"
              className="hidden md:flex items-center p-1 bg-emerald-950/70 rounded-2xl border border-emerald-800/80 gap-1 shadow-inner"
            >
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = activeTab === link.id;
                return (
                  <button
                    key={link.id}
                    type="button"
                    onClick={() => onTabChange(link.id)}
                    className={cn(
                      'flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all duration-200 cursor-pointer',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                      isActive
                        ? 'bg-emerald-800 text-stone-50 shadow-sm border border-emerald-700'
                        : 'text-emerald-200 hover:text-stone-50 bg-transparent hover:bg-emerald-800/40'
                    )}
                  >
                    <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
                    <span>{link.label}</span>
                    {link.badge !== null && (
                      <span
                        className={cn(
                          'text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold leading-none',
                          isActive ? 'bg-amber-200 text-amber-950' : 'bg-emerald-800 text-stone-100 border border-emerald-700'
                        )}
                      >
                        {link.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          )}

          {/* Right Header: Dynamic Profile Header State & Sign Out */}
          <div className="flex items-center gap-2.5 shrink-0">
            {currentUser && (
              <div className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-emerald-800/80 border border-emerald-700/80 text-stone-50">
                <RoleIcon className="w-4 h-4 text-amber-300 shrink-0" />
                <div className="flex flex-col text-left leading-tight">
                  <span className="text-xs font-bold text-stone-50 truncate max-w-[140px]">
                    {currentUser.name}
                  </span>
                  <span className="text-[10px] font-medium text-emerald-200 truncate max-w-[180px]">
                    Operational Unit: {displayUnit}
                  </span>
                </div>
              </div>
            )}

            {/* Simple Sign Out Button */}
            <button
              type="button"
              onClick={handleLogoutClick}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-emerald-700/80 bg-emerald-800/90 hover:bg-emerald-800 hover:border-amber-400/50 text-stone-50 text-xs sm:text-sm font-bold transition-all duration-200 cursor-pointer shadow-xs"
              title="Sign Out of Terminal"
            >
              <LogOut className="w-4 h-4 shrink-0 text-emerald-200" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
