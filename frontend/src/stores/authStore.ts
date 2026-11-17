/**
 * Zustand Auth Store
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { type User, auth, setToken, clearToken } from '../api/client';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const res = await auth.login(email, password);
          setToken(res.access_token);
          set({
            token: res.access_token,
            user: {
              id: res.user_id,
              email: res.email,
              full_name: res.full_name,
              role: res.role as 'USER' | 'ADMIN',
              is_active: true,
              created_at: new Date().toISOString(),
            },
            isLoading: false,
          });
        } catch (err: unknown) {
          set({ error: (err as Error).message, isLoading: false });
          throw err;
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true, error: null });
        try {
          const res = await auth.register(email, password, fullName);
          setToken(res.access_token);
          set({
            token: res.access_token,
            user: {
              id: res.user_id,
              email: res.email,
              full_name: res.full_name,
              role: res.role as 'USER' | 'ADMIN',
              is_active: true,
              created_at: new Date().toISOString(),
            },
            isLoading: false,
          });
        } catch (err: unknown) {
          set({ error: (err as Error).message, isLoading: false });
          throw err;
        }
      },

      logout: () => {
        clearToken();
        set({ user: null, token: null });
      },

      fetchMe: async () => {
        try {
          const user = await auth.me();
          set({ user });
        } catch {
          get().logout();
        }
      },
    }),
    {
      name: 'devcrew-auth',
      partialize: (s) => ({ token: s.token, user: s.user }),
    },
  ),
);
