import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/features/auth/AuthProvider";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { ApiError } from "@/services/api";

export function LoginPage() {
  useDocumentTitle("Sign in · PulseTrace");
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login({ email: email.trim(), password });
      void navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign in failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader title="Sign in" description="Access your workspace and projects" />
      <CardBody>
        <form className="space-y-4" onSubmit={onSubmit}>
          <Input
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Password"
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error ? (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Sign in
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-slate-500">
          No account?{" "}
          <Link className="text-accent-cyan hover:underline" to="/register">
            Create one
          </Link>
        </p>
      </CardBody>
    </Card>
  );
}