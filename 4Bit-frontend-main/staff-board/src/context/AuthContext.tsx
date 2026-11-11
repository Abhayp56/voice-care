import React, { createContext, useContext, useEffect, useState } from 'react';
import { AuthUser, StaffRole } from '../types/complaint';
import { getMyProfile, signIn } from '../api';

interface AuthContextType {
  currentUser: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isRestoring: boolean;
  login: (role: StaffRole, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const TOKEN_KEY = 'voicecare_access_token';
const AuthContext = createContext<AuthContextType | undefined>(undefined);

const roleLabel = (role: string): StaffRole => {
  switch (role) {
    case 'department_staff': throw new Error('Frontline staff accounts are retired. Sign in with a department head or hospital administrator account.');
    case 'department_head': return 'Department Head';
    case 'hospital_admin': return 'Hospital Administrator';
    case 'higher_authority': return 'Higher Authority';
    default: throw new Error('Your account does not have a valid staff role. Contact the system administrator.');
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(() => sessionStorage.getItem(TOKEN_KEY));
  const [isRestoring, setIsRestoring] = useState(Boolean(sessionStorage.getItem(TOKEN_KEY)));

  useEffect(() => {
    if (!accessToken) { setIsRestoring(false); return; }
    getMyProfile(accessToken).then((profile) => {
      setCurrentUser({
        id: profile.id, name: profile.full_name, email: profile.email || '',
        role: roleLabel(profile.role), department: profile.department_name || '',
        departmentId: profile.department_id || undefined, staffId: profile.id,
        loggedInAt: new Date().toISOString(),
      });
    }).catch(() => { sessionStorage.removeItem(TOKEN_KEY); setAccessToken(null); setCurrentUser(null); })
      .finally(() => setIsRestoring(false));
  }, []);

  const login = async (expectedRole: StaffRole, email: string, password: string) => {
    const session = await signIn(email, password);
    const profile = await getMyProfile(session.access_token);
    const actualRole = roleLabel(profile.role);
    if (actualRole !== expectedRole) throw new Error(`This account is registered as ${actualRole}. Select that role to sign in.`);
    sessionStorage.setItem(TOKEN_KEY, session.access_token);
    setAccessToken(session.access_token);
    setCurrentUser({
      id: profile.id, name: profile.full_name, email: profile.email || email,
      role: actualRole, department: profile.department_name || '',
      departmentId: profile.department_id || undefined, staffId: profile.id,
      loggedInAt: new Date().toISOString(),
    });
  };

  const logout = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    setAccessToken(null);
    setCurrentUser(null);
  };

  return <AuthContext.Provider value={{ currentUser, accessToken, isAuthenticated: !!currentUser && !!accessToken, isRestoring, login, logout }}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
