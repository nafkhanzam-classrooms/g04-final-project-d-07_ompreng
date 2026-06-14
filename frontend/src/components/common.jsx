import { formatDisplayText } from "../utils/chatFormat.js";

export function cx(...classes) {
  return classes.filter(Boolean).join(" ").replace(/\s+/g, " ").trim();
}

export function EmptyState({ children, icon, title, detail, className = "" }) {
  return (
    <div
      className={cx(
        "grid min-h-[44px] place-items-center gap-1.5 rounded-[var(--radius-md)] border border-dashed border-slate-200 bg-slate-50/70 p-3 text-center text-[0.78rem] font-bold text-slate-600",
        className,
      )}
    >
      {icon && <IconBadge size="lg">{icon}</IconBadge>}
      {title ? (
        <>
          <strong className="text-[0.82rem] text-slate-700">{title}</strong>
          {detail && <span className="pt-0.5 text-[0.7rem] font-semibold text-slate-500">{detail}</span>}
        </>
      ) : (
        children
      )}
    </div>
  );
}

export function ListRow({ title, detail, actions, onClick, className = "", titleText, leading }) {
  return (
    <div
      className={cx(
        "flex min-h-[42px] items-center gap-2.5 rounded-[var(--radius-md)] border border-transparent bg-white/80 p-2 transition-[border-color,background,transform] duration-[140ms] ease hover:border-slate-200 hover:bg-white",
        className,
      )}
      title={titleText}
    >
      {leading}
      <button className="row-main" type="button" onClick={onClick} disabled={!onClick}>
        <strong>{title || "-"}</strong>
        {detail && <span>{formatDisplayText(detail)}</span>}
      </button>
      {actions}
    </div>
  );
}

const buttonVariants = {
  default:
    "border-border bg-surface text-text shadow-sm hover:-translate-y-px hover:border-primary/30 hover:bg-primary/10",
  primary:
    "border-transparent bg-primary text-white shadow-[0_10px_24px_rgba(37,99,235,0.2)] hover:-translate-y-px hover:bg-[#1d4ed8]",
  secondary:
    "border-primary/25 bg-[#edf3fb] text-primary shadow-sm hover:-translate-y-px hover:border-primary/40 hover:bg-[#dbeafe]",
  "danger-outline":
    "border-danger/30 bg-danger-bg text-danger hover:-translate-y-px hover:border-danger/50 hover:bg-[#fee2e2]",
  danger:
    "border-transparent bg-danger text-white shadow-[0_10px_24px_rgba(220,38,38,0.18)] hover:-translate-y-px hover:bg-[#b91c1c]",
  ghost:
    "border-transparent bg-transparent text-text-muted hover:bg-surface-muted hover:text-text",
};

export function Button({ children, variant = "default", className = "", ...props }) {
  return (
    <button
      className={cx(
        "inline-flex min-h-9 items-center justify-center gap-2 rounded-[var(--radius-md)] border px-3 py-2 text-[0.82rem] font-extrabold transition-[background,border-color,color,transform,box-shadow] duration-[140ms] ease focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60",
        buttonVariants[variant] || buttonVariants.default,
        className,
      )}
      type="button"
      {...props}
    >
      {children}
    </button>
  );
}

export function Panel({ as: Component = "section", className = "", children, ...props }) {
  return (
    <Component
      className={cx(
        "overflow-hidden rounded-[var(--radius-lg)] border border-slate-900/10 bg-white/[0.98] shadow-sm",
        className,
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

export function PanelHeading({ children, className = "", ...props }) {
  return (
    <div className={cx("panel-heading", className)} {...props}>
      {children}
    </div>
  );
}

export function IconBadge({ children, size = "sm", className = "" }) {
  const sizeClass =
    size === "lg"
      ? "h-12 w-12 rounded-[14px]"
      : size === "md"
        ? "h-9 w-9 rounded-full"
        : "h-8 w-8 rounded-[9px]";

  return (
    <span
      className={cx(
        "inline-flex shrink-0 items-center justify-center bg-[#eff6ff] text-primary",
        sizeClass,
        className,
      )}
      aria-hidden="true"
    >
      {children}
    </span>
  );
}

export function Pill({ children, className = "", ...props }) {
  return (
    <span
      className={cx(
        "inline-flex min-h-6 items-center justify-center rounded-full px-2 text-[0.68rem] font-black",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
