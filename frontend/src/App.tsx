import { useState } from "react";
import { Inbox, NotebookPen, MessageSquare } from "lucide-react";
import { useInboxStore } from "./store/useInboxStore";
import { IngestForm } from "./components/IngestForm";
import { ItemsList } from "./components/ItemsList";
import { AskPanel } from "./components/AskPanel";

type MobileTab = "save" | "ask";

function App() {
  const itemCount = useInboxStore((s) => s.items.length);
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
        <span className="font-mono text-xs text-ink-muted bg-surface-sunken border border-border rounded-full px-3 py-1">
          {itemCount} items saved
        </span>
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
