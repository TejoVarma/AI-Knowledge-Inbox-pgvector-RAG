import { Trash2 } from "lucide-react";
import { Badge } from "./Badge";
import { Spinner } from "./Spinner";
import { formatTimestamp } from "../utils/formatTimestamp";
import type { Item } from "../types";

interface ItemCardProps {
  item: Item;
  isDeleting: boolean;
  isRemoving?: boolean;
  onRequestDelete: (item: Item) => void;
}

export function ItemCard({ item, isDeleting, isRemoving = false, onRequestDelete }: ItemCardProps) {
  return (
    <article
      className={`group bg-surface-sunken border border-border rounded-md px-4 py-3 hover:shadow-md transition-shadow animate-card-in ${
        isRemoving ? "card-removing" : ""
      }`}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <Badge type={item.source_type} />
        <button
          onClick={() => onRequestDelete(item)}
          disabled={isDeleting}
          aria-label="Remove item"
          className="ml-auto text-ink-faint hover:text-danger opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-100"
        >
          {isDeleting ? <Spinner size={13} /> : <Trash2 size={13} />}
        </button>
      </div>
      <p className="text-sm text-ink-muted line-clamp-2">{item.content}</p>
      {item.source_ref && (
        <p className="text-xs font-mono text-secondary-ink mt-1 truncate">{item.source_ref}</p>
      )}
      <p className="text-xs font-mono text-ink-faint mt-1.5 text-right">
        {formatTimestamp(item.created_at)}
      </p>
    </article>
  );
}
