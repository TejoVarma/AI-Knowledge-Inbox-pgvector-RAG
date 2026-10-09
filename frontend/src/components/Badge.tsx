import { StickyNote, Link2 } from "lucide-react";
import type { SourceType } from "../types";

interface BadgeProps {
  type: SourceType;
}

const ICONS = { note: StickyNote, url: Link2 };

export function Badge({ type }: BadgeProps) {
  const Icon = ICONS[type];
  const styles =
    type === "url"
      ? "bg-secondary-tint text-secondary-ink"
      : "bg-primary-tint text-primary-ink";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-medium uppercase tracking-wide ${styles}`}
    >
      <Icon size={11} />
      {type}
    </span>
  );
}
