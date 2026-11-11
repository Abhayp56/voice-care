import React, { useState } from 'react';
import {
  HeartPulse,
  Lock,
  Mail,
  ArrowRight,
  Eye,
  EyeOff,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Building2,
  Users,
  Shield,
  Check,
} from 'lucide-react';
import { StaffRole } from '../types/complaint';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

const ROLES: { id: StaffRole; label: string; shortDesc: string; icon: React.ElementType; themeColor: string }[] = [
  {
    id: 'Department Head',
    label: 'Department Head',
    shortDesc: 'Resolve department complaints with photo evidence',
    icon: Users,
    themeColor: 'sky',
  },
  {
    id: 'Hospital Administrator',
    label: 'Hospital Administrator',
    shortDesc: 'Hospital-wide oversight & human review',
    icon: Shield,
    themeColor: 'indigo',
  },
  {
    id: 'Higher Authority',
    label: 'Higher Authority',
    shortDesc: 'Visit, verify, and submit cases overdue by 11 days',
    icon: Shield,
    themeColor: 'sky',
  },
];

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const { login } = useAuth();
  // Role is null by default so credentials remain hidden until a role button is clicked
  const [selectedRole, setSelectedRole] = useState<StaffRole | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRoleSelect = (role: StaffRole) => {
    setSelectedRole(role);
    setErrorMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!selectedRole) {
      setErrorMessage('Please select your hospital role before signing in.');
      return;
    }

    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please enter a valid hospital email address.');
      return;
    }

    if (!password.trim() || password.length < 4) {
      setErrorMessage('Please enter a valid password (minimum 4 characters).');
      return;
    }

    setIsLoading(true);
    try {
      await login(selectedRole, email, password);
      onLoginSuccess();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const credentialsReady = !!selectedRole;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-hospital-950 to-navy-950 flex flex-col justify-between p-4 sm:p-6 lg:p-8 text-slate-100">
      {/* Top Bar: Hospital Branding & Security Telemetry */}
      <header className="max-w-5xl w-full mx-auto flex items-center justify-between py-2 border-b border-white/10 text-xs text-slate-400">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-hospital-500 to-hospital-700 flex items-center justify-center text-white shadow-md shadow-hospital-600/30">
            <HeartPulse className="w-4 h-4" />
          </div>
          <div>
            <span className="font-extrabold text-white text-sm tracking-tight">4BIT VoiceCare</span>
            <span className="ml-2 text-[10px] font-bold uppercase tracking-wider text-hospital-400 bg-hospital-900/60 px-2 py-0.5 rounded border border-hospital-700/60">
              Staff Portal
            </span>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-4 text-[11px] font-mono text-hospital-300">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Hospital Intranet: Geofenced
          </span>
          <span className="bg-white/10 px-2 py-0.5 rounded text-white">Hospital Staff Access</span>
        </div>
      </header>

      {/* Main Centered Login Section */}
      <main className="flex-1 w-full max-w-xl mx-auto flex flex-col items-center justify-center py-8 px-2 sm:px-0">
        <div className="w-full space-y-6">
          {/* Header above card */}
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-hospital-500 to-hospital-700 flex items-center justify-center text-white shadow-xl shadow-hospital-600/30 mx-auto mb-3">
              <HeartPulse className="w-7 h-7" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Hospital Staff &amp; Admin Sign In
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-md mx-auto leading-relaxed">
              Select your designated healthcare role below to enter credentials and access the workspace.
            </p>
          </div>

          {/* Centered Form Card */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 text-stone-900 shadow-sm border border-stone-200 space-y-6">
            {/* Task 1: Three-Button Role Selector */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-black uppercase tracking-wider text-slate-700">
                  Step 1: Select Your Role <span className="text-rose-600">*</span>
                </label>
                <span className="text-[11px] font-mono text-slate-400">
                  {selectedRole ? 'Role Selected' : 'Required to Continue'}
                </span>
              </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {ROLES.map((role) => {
                  const Icon = role.icon;
                  const isSelected = selectedRole === role.id;

                  // Active vs Unselected styles
                  const selectedClasses = {
                    'Department Head': 'border-sky-600 bg-sky-50 text-sky-950 ring-2 ring-sky-500/30 shadow-md',
                    'Hospital Administrator': 'border-indigo-600 bg-indigo-50 text-indigo-950 ring-2 ring-indigo-500/30 shadow-md',
                    'Higher Authority': 'border-sky-600 bg-sky-50 text-sky-950 ring-2 ring-sky-500/30 shadow-md',
                  }[role.id];

                  const iconColor = isSelected
                    ? {
                        'Department Head': 'text-sky-700 bg-sky-200/80',
                        'Hospital Administrator': 'text-indigo-700 bg-indigo-200/80',
                        'Higher Authority': 'text-sky-700 bg-sky-200/80',
                      }[role.id]
                    : 'text-slate-500 bg-slate-100';

                  return (
                    <button
                      key={role.id}
                      type="button"
                      onClick={() => handleRoleSelect(role.id)}
                      className={`relative p-3.5 rounded-2xl border-2 text-left transition-all duration-200 cursor-pointer flex flex-col justify-between gap-2.5 ${
                        isSelected
                          ? selectedClasses
                          : 'border-slate-200 bg-slate-50/70 hover:border-slate-300 hover:bg-slate-100/90 text-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${iconColor}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        {isSelected && (
                          <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </span>
                        )}
                      </div>

                      <div>
                        <div className="font-black text-sm leading-snug">{role.label}</div>
                        <div className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5 line-clamp-2">
                          {role.shortDesc}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {errorMessage && (
              <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Task 2: Dynamic Credential Entry */}
            {selectedRole && credentialsReady ? (
              <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-slate-100 animate-fade-in">
                <div className="flex items-center justify-between text-xs pb-1">
                  <span className="font-black uppercase tracking-wider text-slate-700">
                    Step 2: Enter {selectedRole} Credentials
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium">
                    Sign in with your registered hospital account.
                  </span>
                </div>

                {/* Email Input with dynamic label & placeholder */}
                <div className="space-y-1.5">
                  <label htmlFor="emailInput" className="block text-xs font-black uppercase tracking-wider text-slate-700">
                    {selectedRole} Email Address <span className="text-rose-600">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      id="emailInput"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={`Enter ${selectedRole} email`}
                      required
                      className="w-full bg-slate-50 border-2 border-slate-300 rounded-2xl py-3 pl-10 pr-4 text-sm font-bold text-slate-900 focus:outline-none focus:border-hospital-500 focus:bg-white focus:ring-4 focus:ring-hospital-500/10 transition"
                    />
                  </div>
                </div>

                {/* Password Input with dynamic label */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label htmlFor="passwordInput" className="block text-xs font-black uppercase tracking-wider text-slate-700">
                      {selectedRole} Security Password <span className="text-rose-600">*</span>
                    </label>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      id="passwordInput"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={`Enter ${selectedRole} password`}
                      required
                      className="w-full bg-slate-50 border-2 border-slate-300 rounded-2xl py-3 pl-10 pr-10 text-sm font-bold text-slate-900 focus:outline-none focus:border-hospital-500 focus:bg-white focus:ring-4 focus:ring-hospital-500/10 transition font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Terminal Geofence Status */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-slate-700 font-medium">
                    <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Access check: <strong>Supabase Auth and staff profile</strong></span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 font-bold px-2 py-0.5 rounded">
                    VERIFIED
                  </span>
                </div>

                {/* Dynamic Submit Button */}
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  isLoading={isLoading}
                  className="w-full font-black text-base shadow-lg shadow-hospital-600/20 py-3.5 mt-2"
                  rightIcon={<ArrowRight className="w-5 h-5" />}
                >
                  Sign in to {selectedRole} Portal
                </Button>
              </form>
            ) : (
              /* Helpful prompt state before a role button is clicked */
              <div className="p-6 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50/60 text-center space-y-1.5 animate-fade-in">
                <p className="text-xs font-bold text-slate-700">
                  Please select your hospital role above
                </p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                  Credential fields will be revealed dynamically based on your chosen access tier.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer Disclaimer */}
      <footer className="max-w-5xl w-full mx-auto text-center py-3 border-t border-white/10 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Supabase authenticated staff access
        </span>
        <span className="text-slate-400 font-mono text-[11px] flex items-center gap-1">
          <Building2 className="w-3.5 h-3.5 text-slate-500" />
          4BIT VoiceCare Staff Portal
        </span>
      </footer>
    </div>
  );
};

export default LoginPage;
