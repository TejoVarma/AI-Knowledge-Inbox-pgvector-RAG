import { useEffect, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router";
import { useAuthStore } from "./store/useAuthStore";
import { AuthScreen } from "./components/AuthScreen";
import { InboxScreen } from "./components/InboxScreen";
import { ServerUnreachable } from "./components/ServerUnreachable";
import { Spinner } from "./components/Spinner";

function App() {
  const status = useAuthStore((s) => s.status);
  const checkSession = useAuthStore((s) => s.checkSession);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  // the back/forward cache can restore a frozen copy of this page from before a logout -
  // notes and all - without re-running anything. ask the backend again when that happens
  useEffect(() => {
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) checkSession();
    };
    window.addEventListener("pageshow", onPageShow);
    return () => window.removeEventListener("pageshow", onPageShow);
  }, [checkSession]);

  // nothing is routed until we know who's here, so a logged-in refresh of /inbox never
  // flashes the login page and a logged-out visit never flashes the inbox
  if (status === "checking") {
    return (
      <div className="h-screen flex items-center justify-center text-ink-muted">
        <Spinner size={22} />
      </div>
    );
  }
  if (status === "unreachable") return <ServerUnreachable onRetry={checkSession} />;

  const home = status === "authenticated" ? "/inbox" : "/login";

  return (
    <Routes>
      <Route path="/login" element={<GuestOnly><AuthScreen mode="login" /></GuestOnly>} />
      <Route path="/register" element={<GuestOnly><AuthScreen mode="register" /></GuestOnly>} />
      <Route path="/inbox" element={<RequireAuth><InboxScreen /></RequireAuth>} />
      <Route path="*" element={<Navigate to={home} replace />} />
    </Routes>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);
  return status === "authenticated" ? children : <Navigate to="/login" replace />;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);
  return status === "authenticated" ? <Navigate to="/inbox" replace /> : children;
}

export default App;
