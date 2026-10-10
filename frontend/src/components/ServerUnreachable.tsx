import { CloudOff, RotateCw } from "lucide-react";

export function ServerUnreachable({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm bg-surface border border-border rounded-lg shadow-sm p-6 flex flex-col items-center gap-3 text-center">
        <CloudOff size={28} className="text-ink-faint" />
        <h2 className="font-display text-lg font-semibold">Can't reach the server</h2>
        <p className="text-sm text-ink-muted">
          It may be starting up — the free hosting sleeps when nobody's using it and takes up to a minute to wake.
        </p>
        <button
          onClick={onRetry}
          className="flex items-center gap-2 bg-primary text-white rounded-md px-4 py-2.5 text-sm font-semibold"
        >
          <RotateCw size={14} />
          Try again
        </button>
      </div>
    </div>
  );
}
