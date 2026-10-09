import { useEffect } from "react";
import { Spinner } from "./Spinner";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  isConfirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  isConfirming = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  return (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50"
      onClick={onCancel}
    >
      <div
        className="bg-surface border border-border rounded-lg shadow-lift p-6 max-w-sm w-full animate-modal-in"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-display text-lg font-semibold mb-2">{title}</h3>
        <p className="text-sm text-ink-muted mb-6">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="text-sm font-medium text-ink-muted px-4 py-2 rounded-md hover:bg-surface-sunken transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isConfirming}
            className="bg-danger text-white text-sm font-semibold px-4 py-2 rounded-md disabled:opacity-50 hover:opacity-90 transition-opacity inline-flex items-center gap-2"
          >
            {isConfirming && <Spinner size={13} />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
