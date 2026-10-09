import { useEffect, useState } from "react";
import { Send, Shuffle } from "lucide-react";
import { useInboxStore } from "../store/useInboxStore";
import { AnswerText } from "./AnswerText";
import { SourceCard } from "./SourceCard";
import { Spinner } from "./Spinner";
import { TypingIndicator } from "./TypingIndicator";
import { pickRandom } from "../utils/pickRandom";

const SUGGESTION_COUNT = 4;

export function AskPanel() {
  const question = useInboxStore((s) => s.question);
  const setQuestion = useInboxStore((s) => s.setQuestion);
  const ask = useInboxStore((s) => s.ask);
  const isAsking = useInboxStore((s) => s.isAsking);
  const answer = useInboxStore((s) => s.answer);
  const sources = useInboxStore((s) => s.sources);
  const askError = useInboxStore((s) => s.askError);
  const items = useInboxStore((s) => s.items);

  const questionPool = items
    .map((item) => item.suggested_question)
    .filter((q): q is string => Boolean(q));

  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    setSuggestions(pickRandom(questionPool, SUGGESTION_COUNT));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items.length]);

  const shuffleSuggestions = () => setSuggestions(pickRandom(questionPool, SUGGESTION_COUNT));

  return (
    <section
      className={`bg-surface border border-border rounded-lg shadow-sm p-6 flex flex-col min-h-0 ${
        isAsking || answer ? "flex-1" : ""
      }`}
    >
      <h2 className="font-display text-lg font-semibold mb-4 flex-none">Ask a question</h2>

      <div className="flex gap-2 flex-none">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="What did you save about…"
          className="flex-1 bg-surface-sunken border border-border rounded-md px-3.5 py-2.5 text-sm placeholder:text-ink-faint"
        />
        <button
          onClick={ask}
          disabled={isAsking || !question.trim()}
          className="bg-secondary text-white text-sm font-semibold px-5 py-2.5 rounded-md disabled:opacity-50 hover:opacity-90 transition-opacity inline-flex items-center gap-2"
        >
          {isAsking ? <Spinner size={14} /> : <Send size={14} />}
          {isAsking ? "Asking…" : "Ask"}
        </button>
      </div>

      {suggestions.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mt-3 flex-none">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuestion(s);
                ask();
              }}
              className="text-xs font-mono text-ink-muted bg-surface-sunken border border-border rounded-full px-3 py-1 hover:border-secondary hover:text-secondary-ink transition-colors"
            >
              {s}
            </button>
          ))}
          {questionPool.length > SUGGESTION_COUNT && (
            <button
              onClick={shuffleSuggestions}
              aria-label="Shuffle suggestions"
              className="text-ink-faint hover:text-secondary-ink transition-colors p-1"
            >
              <Shuffle size={13} />
            </button>
          )}
        </div>
      )}

      {askError && <p className="text-danger text-sm mt-4 flex-none">{askError}</p>}

      {(isAsking || answer) && (
        <div className="mt-6 pt-5 border-t border-dashed border-border flex-1 min-h-0 overflow-y-auto">
          <p className="text-xs font-mono uppercase tracking-wide text-ink-faint mb-2">Answer</p>

          {isAsking ? (
            <TypingIndicator />
          ) : (
            <div key={question} className="animate-answer-in">
              <AnswerText text={answer!} />

              {sources.length > 0 && (
                <>
                  <p className="text-xs font-mono uppercase tracking-wide text-ink-faint mt-5 mb-2">
                    Sources
                  </p>
                  <div className="flex flex-col gap-2">
                    {sources.map((s, i) => (
                      <SourceCard key={i} source={s} index={i + 1} />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
