import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
} from "@/services/auth";
import { ApiError } from "@/services/api";
import { clearToken, getToken } from "@/services/auth-session";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  authError: string | null;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: fetchCurrentUser,
    retry: false,
    staleTime: 60_000,
    enabled: getToken() !== null,
  });

  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      queryClient.setQueryData(["auth", "me"], data.user);
    },
  });

  const registerMutation = useMutation({
    mutationFn: registerUser,
  });

  const logoutMutation = useMutation({
    mutationFn: logoutUser,
    onSuccess: () => {
      clearToken();
      queryClient.setQueryData(["auth", "me"], null);
      queryClient.removeQueries({ queryKey: ["projects"] });
    },
    onSettled: () => {
      clearToken();
    },
  });

  const login = useCallback(
    async (payload: LoginPayload) => {
      await loginMutation.mutateAsync(payload);
    },
    [loginMutation]
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      await registerMutation.mutateAsync(payload);
      await loginMutation.mutateAsync({
        email: payload.email,
        password: payload.password,
      });
    },
    [loginMutation, registerMutation]
  );

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const refreshUser = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
  }, [queryClient]);

  const authError = useMemo(() => {
    const err = loginMutation.error ?? registerMutation.error ?? meQuery.error;
    if (err instanceof ApiError) return err.message;
    if (err instanceof Error) return err.message;
    return null;
  }, [loginMutation.error, registerMutation.error, meQuery.error]);

  const sessionTokenPresent = typeof window !== "undefined" && getToken() !== null;

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.isError && !sessionTokenPresent ? null : (meQuery.data ?? null),
      isLoading:
        sessionTokenPresent &&
        (meQuery.isLoading || (meQuery.isPending && meQuery.fetchStatus !== "idle")),
      isAuthenticated:
        sessionTokenPresent &&
        Boolean(meQuery.data) &&
        !meQuery.isError,
      login,
      register,
      logout,
      refreshUser,
      authError,
    }),
    [
      authError,
      login,
      logout,
      meQuery.data,
      meQuery.isError,
      meQuery.fetchStatus,
      meQuery.isLoading,
      meQuery.isPending,
      refreshUser,
      register,
      sessionTokenPresent,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}