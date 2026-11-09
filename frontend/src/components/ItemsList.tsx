import { useEffect, useState } from "react";
import { useInboxStore } from "../store/useInboxStore";
import { ItemCard } from "./ItemCard";
import { Spinner } from "./Spinner";
import { ConfirmDialog } from "./ConfirmDialog";
import type { Item } from "../types";

const REMOVE_ANIMATION_MS = 180;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function ItemsList() {
  const items = useInboxStore((s) => s.items);
  const fetchItems = useInboxStore((s) => s.fetchItems);
  const isLoadingItems = useInboxStore((s) => s.isLoadingItems);
  const itemsError = useInboxStore((s) => s.itemsError);
  const removeItem = useInboxStore((s) => s.removeItem);
  const deletingIds = useInboxStore((s) => s.deletingIds);

  const [pendingDelete, setPendingDelete] = useState<Item | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const isConfirmingDelete = pendingDelete ? deletingIds.includes(pendingDelete.id) : false;

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    const id = pendingDelete.id;
    setPendingDelete(null);
    setRemovingId(id);
    await sleep(REMOVE_ANIMATION_MS);
    await removeItem(id);
    setRemovingId(null);
  };

  return (
    <section className="bg-surface border border-border rounded-lg shadow-sm p-6 flex-1 min-h-0 flex flex-col">
      <h2 className="font-display text-lg font-semibold mb-4 flex-none">
        Saved items <span className="text-ink-faint text-xs font-mono font-normal">{items.length}</span>
      </h2>

      {isLoadingItems && (
        <div className="flex items-center gap-2 text-sm text-ink-muted py-4">
          <Spinner className="text-secondary" />
          Loading…
        </div>
      )}

      {itemsError && (
        <div
          role="alert"
          className="flex-none flex items-center justify-between gap-3 text-sm text-danger border border-danger/30 bg-danger/5 rounded-md px-3 py-2 mb-3"
        >
          <span>{itemsError}</span>
          <button type="button" onClick={fetchItems} className="flex-none font-medium underline">
            Try again
          </button>
        </div>
      )}

      {/* after a failed load the list is empty because we don't know, not because nothing is saved */}
      {!isLoadingItems && !itemsError && items.length === 0 && (
        <p className="text-sm text-ink-faint py-6 text-center">
          Nothing saved yet — add a note or URL to get started.
        </p>
      )}

      <div className="flex flex-col gap-2 flex-1 min-h-0 overflow-y-auto">
        {items.map((item) => (
          <ItemCard
            key={item.id}
            item={item}
            isDeleting={deletingIds.includes(item.id)}
            isRemoving={removingId === item.id}
            onRequestDelete={setPendingDelete}
          />
        ))}
      </div>

      {pendingDelete && (
        <ConfirmDialog
          title="Remove this item?"
          message="This will permanently delete it along with its saved chunks. This can't be undone."
          confirmLabel="Delete"
          isConfirming={isConfirmingDelete}
          onConfirm={handleConfirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </section>
  );
}
