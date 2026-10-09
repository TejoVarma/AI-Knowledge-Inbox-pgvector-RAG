import { useState } from "react";
import { StickyNote, Link2, Plus } from "lucide-react";
import { useInboxStore } from "../store/useInboxStore";
import { Spinner } from "./Spinner";
import { isBareUrl } from "../utils/isBareUrl";
import type { SourceType } from "../types";

const TAB_ICONS = { note: StickyNote, url: Link2 };

export function IngestForm() {
  const [sourceType, setSourceType] = useState<SourceType>("note");
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");
  const saveItem = useInboxStore((s) => s.saveItem);
  const isSaving = useInboxStore((s) => s.isSaving);
  const saveError = useInboxStore((s) => s.saveError);
  const clearSaveError = useInboxStore((s) => s.clearSaveError);

  const isBareUrlInNote = sourceType === "note" && isBareUrl(content);

  const handleSave = async () => {
    const payload =
      sourceType === "note"
        ? { source_type: "note" as const, content: content.trim() }
        : { source_type: "url" as const, url: url.trim() };

    const result = await saveItem(payload);
    if (result.ok) {
      setContent("");
      setUrl("");
    }
  };

  return (
    <section className="bg-surface border border-border rounded-lg shadow-sm p-6 flex-none">
      <h2 className="font-display text-lg font-semibold mb-4">Save something</h2>

      <div className="inline-flex bg-surface-sunken border border-border rounded-md p-1 mb-4">
        {(["note", "url"] as const).map((type) => {
          const Icon = TAB_ICONS[type];
          return (
            <button
              key={type}
              onClick={() => {
                setSourceType(type);
                clearSaveError();
              }}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-sm text-sm font-medium capitalize transition-colors ${
                sourceType === type
                  ? "bg-surface shadow-sm text-ink"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              <Icon size={14} />
              {type}
            </button>
          );
        })}
      </div>

      {sourceType === "note" ? (
        <textarea
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            clearSaveError();
          }}
          placeholder="Paste a note…"
          rows={2}
          className="w-full bg-surface-sunken border border-border rounded-md px-3.5 py-2.5 text-sm resize-none placeholder:text-ink-faint"
        />
      ) : (
        <input
          type="text"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            clearSaveError();
          }}
          placeholder="https://en.wikipedia.org/wiki/..."
          className="w-full bg-surface-sunken border border-border rounded-md px-3.5 py-2.5 text-sm placeholder:text-ink-faint"
        />
      )}

      <div className="flex items-center justify-between mt-3">
        <span className="text-xs text-ink-faint">
          {sourceType === "note" ? "Plain text only" : "Must be a public page"}
        </span>
        <button
          onClick={handleSave}
          disabled={
            isSaving ||
            isBareUrlInNote ||
            (sourceType === "note" ? !content.trim() : !url.trim())
          }
          className="bg-primary text-white text-sm font-semibold px-5 py-2 rounded-md disabled:opacity-50 hover:opacity-90 transition-opacity inline-flex items-center gap-2"
        >
          {isSaving ? <Spinner size={14} /> : <Plus size={14} />}
          {isSaving ? "Saving…" : "Save"}
        </button>
      </div>

      {isBareUrlInNote && (
        <p className="text-danger text-xs mt-2">
          That's just a URL — switch to the URL tab to save it properly.
        </p>
      )}
      {saveError && <p className="text-danger text-xs mt-2">{saveError}</p>}
    </section>
  );
}
