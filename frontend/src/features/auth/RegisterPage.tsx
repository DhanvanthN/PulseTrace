import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/features/auth/AuthProvider";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { ApiError } from "@/services/api";

function validatePassword(value: string): string | null {
  if (value.length < 8) return "Password must be at least 8 characters";
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) {
    return "Password must include at least one letter and one number";
  }
  return null;
}

export function RegisterPage() {
  useDocumentTitle("Register · PulseTrace");
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const validation = validatePassword(password);
    setPasswordError(validation);
    if (validation) return;

    setIsLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
      });
      void navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="Create account"
        description="Register to create projects and connect observability data"
      />
      <CardBody>
        <form className="space-y-4" onSubmit={onSubmit}>
          <Input
            label="Full name"
            name="full_name"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
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
            autoComplete="new-password"
            required
            value={password}
            error={passwordError ?? undefined}
            onChange={(e) => {
              setPassword(e.target.value);
              setPasswordError(null);
            }}
          />
          {error ? (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Create account
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-slate-500">
          Already registered?{" "}
          <Link className="text-accent-cyan hover:underline" to="/login">
            Sign in
          </Link>
        </p>
      </CardBody>
    </Card>
  );
}