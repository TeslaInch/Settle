"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { type ApiResponse } from "./api";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (...args: Parameters<(...a: never[]) => Promise<ApiResponse<T>>>) => Promise<T | null>;
  reset: () => void;
}

/**
 * Wraps any API call with loading/error/success state.
 * Automatically handles:
 * - 401 → redirect to /login with session-expired message
 * - Network error (status 0) → friendly message
 */
export function useApi<T, Args extends unknown[]>(
  apiFn: (...args: Args) => Promise<ApiResponse<T>>
): {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
} {
  const router = useRouter();
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setState({ data: null, loading: true, error: null });

      const res = await apiFn(...args);

      if (res.status === 401) {
        // Session expired — clear token and redirect
        if (typeof window !== "undefined") {
          localStorage.removeItem("settle_token");
          localStorage.removeItem("settle_user");
        }
        router.push("/login?reason=session_expired");
        return null;
      }

      if (res.status === 0) {
        setState({
          data: null,
          loading: false,
          error: "Check your connection and try again.",
        });
        return null;
      }

      if (res.error || !res.data) {
        setState({
          data: null,
          loading: false,
          error: res.error ?? "Something went wrong.",
        });
        return null;
      }

      setState({ data: res.data, loading: false, error: null });
      return res.data;
    },
    [apiFn, router]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
