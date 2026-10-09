const PULSE_DURATION_MS = 1800;

function jumpToSource(n: string) {
  const el = document.getElementById(`source-${n}`);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  el.classList.add("pulse-highlight");
  setTimeout(() => el.classList.remove("pulse-highlight"), PULSE_DURATION_MS);
}

interface AnswerTextProps {
  text: string;
}

export function AnswerText({ text }: AnswerTextProps) {
  const parts = text.split(/(\[\d+\])/g);

  return (
    <p className="font-display text-[17px] leading-relaxed text-ink">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) return <span key={i}>{part}</span>;

        const n = match[1];
        return (
          <button
            key={i}
            onClick={() => jumpToSource(n)}
            className="inline-flex items-center justify-center align-super text-[11px] font-mono font-semibold text-highlight-ink bg-highlight-tint px-1.5 rounded-sm mx-0.5 hover:bg-highlight/40 transition-colors"
          >
            {n}
          </button>
        );
      })}
    </p>
  );
}
