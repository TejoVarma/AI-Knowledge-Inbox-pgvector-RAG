import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router";
import { Inbox } from "lucide-react";
import { useAuthStore } from "../store/useAuthStore";
import { Spinner } from "./Spinner";

type Mode = "login" | "register";

const inputClass =
  "w-full bg-surface-sunken border border-border rounded-md px-3.5 py-2.5 text-sm placeholder:text-ink-faint";

export function AuthScreen({ mode }: { mode: Mode }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const sessionExpired = useAuthStore((s) => s.sessionExpired);
  const isSubmitting = useAuthStore((s) => s.isSubmitting);

  const isRegister = mode === "register";
  const passwordTooShort = isRegister && password.length > 0 && password.length < 8;
  const canSubmit =
    email.trim() && password && (!isRegister || (name.trim() && password.length >= 8)) && !isSubmitting;

  // a message from the other screen ("invalid email or password") shouldn't follow you here
  useEffect(() => {
    clearError();
  }, [mode, clearError]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    if (isRegister) register(name.trim(), email.trim(), password);
    else login(email.trim(), password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-3 mb-8">
          <span className="w-9 h-9 rounded-md bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Inbox size={19} className="text-white" strokeWidth={2.25} />
          </span>
          <h1 className="font-display text-2xl font-semibold tracking-tight">Knowledge Inbox</h1>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-lg shadow-sm p-6 flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">
            {isRegister ? "Create your account" : "Welcome back"}
          </h2>

          {sessionExpired && !isRegister && (
            <p className="text-sm text-highlight-ink bg-highlight-tint rounded-md px-3.5 py-2.5">
              Your session expired. Please log in again.
            </p>
          )}

          {isRegister && (
            <label className="flex flex-col gap-1.5 text-sm font-medium">
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                maxLength={100}
                placeholder="Your name"
                className={inputClass}
              />
            </label>
          )}

          <label className="flex flex-col gap-1.5 text-sm font-medium">
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1.5 text-sm font-medium">
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              maxLength={128}
              placeholder={isRegister ? "At least 8 characters" : "Your password"}
              className={inputClass}
            />
            {passwordTooShort && (
              <span className="text-xs font-normal text-ink-faint">At least 8 characters</span>
            )}
          </label>

          {error && (
            <p role="alert" className="text-sm text-danger bg-danger-tint rounded-md px-3.5 py-2.5">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!canSubmit}
            className="flex items-center justify-center gap-2 bg-primary text-white rounded-md py-2.5 text-sm font-semibold transition-opacity disabled:opacity-50"
          >
            {isSubmitting && <Spinner size={14} />}
            {isRegister ? "Create account" : "Log in"}
          </button>
        </form>

        <p className="text-center text-sm text-ink-muted mt-5">
          {isRegister ? "Already have an account?" : "New here?"}{" "}
          <Link to={isRegister ? "/login" : "/register"} className="font-semibold text-secondary-ink hover:underline">
            {isRegister ? "Log in" : "Create an account"}
          </Link>
        </p>
      </div>
    </div>
  );
}
