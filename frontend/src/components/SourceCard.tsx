import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { SourceSnippet } from "../types";

const TRUNCATE_THRESHOLD = 140;

interface SourceCardProps {
  source: SourceSnippet;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLong = source.chunk_text.length > TRUNCATE_THRESHOLD;

  return (
    <div
      id={`source-${index}`}
      className="bg-surface-sunken border border-border border-l-4 border-l-highlight rounded-r-md px-3.5 py-2.5 scroll-mt-4"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-mono text-highlight-ink font-medium">
          [{index}] {source.source_type}
        </span>
        <span className="text-xs font-mono text-ink-faint ml-auto">
          similarity {source.similarity.toFixed(3)}
        </span>
      </div>
      <p className={`text-xs text-ink-muted ${isLong && !isExpanded ? "line-clamp-2" : ""}`}>
        {source.chunk_text}
      </p>
      {isLong && (
        <button
          onClick={() => setIsExpanded((v) => !v)}
          className="flex items-center gap-1 text-xs font-medium text-secondary-ink mt-1.5 hover:opacity-75 transition-opacity"
        >
          {isExpanded ? "Show less" : "Show more"}
          {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      )}
    </div>
  );
}
