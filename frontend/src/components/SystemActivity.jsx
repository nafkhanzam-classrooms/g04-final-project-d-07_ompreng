import { formatDisplayText } from "../utils/chatFormat.js";
import { EmptyState, PanelHeading, Pill, cx } from "./common.jsx";

export function SystemActivity({ chat }) {
  return (
    <details className="overflow-hidden rounded-b-[var(--radius-lg)] border-0 bg-white/[0.98] shadow-none">
      <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
        <PanelHeading>
          <h2 id="logsTitle" className="text-[1.05rem] font-extrabold text-text">
            System Activity
          </h2>
          <Pill className="ml-auto max-w-full gap-1.5 overflow-hidden text-ellipsis whitespace-nowrap border border-slate-900/10 bg-white px-[11px] text-[0.78rem] text-text-muted">
            <span className="font-semibold text-text-muted">Last activity:</span>
            <span>{chat.lastRequest || "Idle"}</span>
          </Pill>
        </PanelHeading>
      </summary>

      <div
        className="log-list grid max-h-[300px] content-start gap-2 overflow-auto p-2.5"
        aria-live="polite"
      >
        {chat.serverLogs.length ? (
          chat.serverLogs.map((log) => (
            <div
              key={log.id}
              className={cx(
                "flex min-h-[46px] items-center gap-2.5 rounded-[var(--radius-md)] border bg-white p-2.5 transition-[border-color,background,transform] duration-[140ms]",
                log.tone === "success" && "border-success/30 bg-[#eff8f2]",
                log.tone === "error" && "border-danger/35 bg-[#fff5f5]",
                log.tone === "sent" && "border-primary/30 bg-[#edf3fb]",
                !["success", "error", "sent"].includes(log.tone) && "border-border",
              )}
            >
              {log.meta && <strong>{log.meta}</strong>}
              <span>{formatDisplayText(log.content || "-")}</span>
            </div>
          ))
        ) : (
          <EmptyState>No activity yet.</EmptyState>
        )}
      </div>
    </details>
  );
}
