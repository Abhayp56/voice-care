import React from 'react';
import {
  CheckSquare,
  BarChart3,
  AlertTriangle,
  Users,
  LogOut,
} from 'lucide-react';
import { StaffRole } from '../../types/complaint';
import { cn } from '../../utils/cn';
import { ActiveTab } from './Header';

export interface BottomNavProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  currentRole: StaffRole;
  onLogout?: () => void;
  overdueCount: number;
  myTasksCount: number;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  onTabChange,
  currentRole,
  onLogout,
  overdueCount,
  myTasksCount,
}) => {
  const getNavItems = () => {
    if (currentRole === 'Department Head') {
      return [
        {
          id: 'grievances' as const,
          label: 'Department',
          shortLabel: 'Grievances',
          icon: CheckSquare,
          badge: myTasksCount,
          badgeColor: 'bg-emerald-900 text-stone-50',
        },
        {
          id: 'workload' as const,
          label: 'Workload',
          shortLabel: 'Team',
          icon: Users,
          badge: null,
          badgeColor: '',
        },
      ];
    }

    // Hospital Administrator: Mutually Exclusive Tabs ("All Departments" and "Escalation Queue")
    return [
      {
        id: 'overview' as const,
        label: 'All Departments',
        shortLabel: 'Overview',
        icon: BarChart3,
        badge: null,
        badgeColor: '',
      },
      {
        id: 'escalations' as const,
        label: 'Escalation Queue',
        shortLabel: 'Escalations',
        icon: AlertTriangle,
        badge: overdueCount > 0 ? overdueCount : null,
        badgeColor: 'bg-amber-50 text-amber-700 border border-amber-200/60 font-bold',
      },
    ];
  };

  const navItems = getNavItems();

  return (
    <nav
      aria-label="Mobile Navigation Bar"
      className="fixed bottom-0 left-0 right-0 w-full z-40 bg-white/95 backdrop-blur-lg border-t border-stone-200/90 shadow-sm md:hidden pb-[max(0.5rem,env(safe-area-inset-bottom))]"
    >
      <div className={`grid grid-cols-${navItems.length + (onLogout ? 1 : 0)} gap-1 px-2 py-1.5 max-w-md mx-auto`}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            activeTab === item.id ||
            (item.id === 'grievances' && activeTab === 'tasks') ||
            (item.id === 'workload' && activeTab === 'overview') ||
            ((currentRole === 'Hospital Administrator' || currentRole === 'Higher Authority') && item.id === 'overview' && activeTab === 'tasks');

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              className={cn(
                'relative min-h-[50px] flex flex-col items-center justify-center rounded-2xl py-1 px-1 select-none transition-all duration-200 cursor-pointer',
                'active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400',
                isActive
                  ? 'text-emerald-950 bg-emerald-50/90 font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800 font-semibold'
              )}
            >
              {isActive && (
                <span className="absolute top-1 w-6 h-1 rounded-full bg-emerald-900" />
              )}

              <div className="relative flex items-center justify-center mt-1">
                <Icon
                  className={cn(
                    'w-5 h-5 transition-transform duration-200',
                    isActive ? 'scale-110' : 'scale-100 opacity-75'
                  )}
                  aria-hidden="true"
                />
                {item.badge !== null && (
                  <span
                    className={cn(
                      'absolute -top-1.5 -right-2 text-[9px] min-w-[16px] h-4 px-1 rounded-full font-mono font-bold flex items-center justify-center',
                      item.badgeColor
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </div>

              <span className="text-[11px] tracking-tight leading-tight mt-1 text-center truncate max-w-full">
                {item.shortLabel}
              </span>
            </button>
          );
        })}

        {/* Mobile Sign Out Button */}
        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="relative min-h-[50px] flex flex-col items-center justify-center rounded-2xl py-1 px-1 select-none transition-all duration-150 text-slate-500 hover:text-rose-600 active:scale-95 cursor-pointer font-bold"
            title="Sign Out of Terminal"
          >
            <div className="relative flex items-center justify-center mt-1">
              <LogOut className="w-5 h-5 opacity-75" aria-hidden="true" />
            </div>
            <span className="text-[11px] tracking-tight leading-tight mt-1 text-center truncate max-w-full font-bold">
              Sign Out
            </span>
          </button>
        )}
      </div>
    </nav>
  );
};

export default BottomNav;
