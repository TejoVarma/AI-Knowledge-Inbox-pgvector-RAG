import { useEffect, useState } from "react";
import { Inbox, NotebookPen, MessageSquare, LogOut } from "lucide-react";
import { useInboxStore } from "./store/useInboxStore";
import { useAuthStore } from "./store/useAuthStore";
import { IngestForm } from "./components/IngestForm";
import { ItemsList } from "./components/ItemsList";
import { AskPanel } from "./components/AskPanel";
import { AuthScreen } from "./components/AuthScreen";
import { Spinner } from "./components/Spinner";

type MobileTab = "save" | "ask";

function App() {
  const status = useAuthStore((s) => s.status);
  const checkSession = useAuthStore((s) => s.checkSession);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  if (status === "checking") {
    return (
      <div className="h-screen flex items-center justify-center text-ink-muted">
        <Spinner size={22} />
      </div>
    );
  }

  // the inbox only mounts once logged in, so it never asks for notes without a session
  return status === "authenticated" ? <InboxScreen /> : <AuthScreen />;
}

function InboxScreen() {
  const itemCount = useInboxStore((s) => s.items.length);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [mobileTab, setMobileTab] = useState<MobileTab>("save");

  return (
    <div className="h-screen flex flex-col">
      <header className="flex-none flex items-center justify-between gap-4 px-7 py-5 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-md bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Inbox size={17} className="text-white" strokeWidth={2.25} />
          </span>
          <h1 className="font-display text-2xl font-semibold tracking-tight">Knowledge Inbox</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline font-mono text-xs text-ink-muted bg-surface-sunken border border-border rounded-full px-3 py-1">
            {itemCount} items saved
          </span>
          <span className="text-sm text-ink-muted">
            Hi, <span className="font-semibold text-ink">{user?.name ?? user?.email}</span>
          </span>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-sm font-medium text-ink-muted hover:text-ink border border-border rounded-md px-3 py-1.5 transition-colors"
          >
            <LogOut size={14} />
            Log out
          </button>
        </div>
      </header>

      <div className="md:hidden flex-none flex border-b border-border">
        {(
          [
            { key: "save", label: "Save", icon: NotebookPen },
            { key: "ask", label: "Ask", icon: MessageSquare },
          ] as const
        ).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setMobileTab(key)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium border-b-2 transition-colors ${
              mobileTab === key
                ? "border-secondary text-ink"
                : "border-transparent text-ink-faint"
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      <main className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 gap-7 p-7 max-w-[1180px] mx-auto w-full">
        <div
          className={`flex-col gap-5 min-h-0 ${mobileTab === "save" ? "flex" : "hidden"} md:flex`}
        >
          <IngestForm />
          <ItemsList />
        </div>
        <div
          className={`flex-col gap-5 min-h-0 overflow-y-auto ${
            mobileTab === "ask" ? "flex" : "hidden"
          } md:flex`}
        >
          <AskPanel />
        </div>
      </main>
    </div>
  );
}

export default App;
