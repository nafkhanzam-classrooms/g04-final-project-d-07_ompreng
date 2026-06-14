import { AccessPanel } from "./components/AccessPanel.jsx";
import { ManageUsersPanel } from "./components/ManageUsersPanel.jsx";
import { MessageCenter } from "./components/MessageCenter.jsx";
import { OnlineUsersPanel } from "./components/OnlineUsersPanel.jsx";
import { PendingRequestsPanel } from "./components/PendingRequestsPanel.jsx";
import { RejectDialog } from "./components/RejectDialog.jsx";
import { RoomPanel } from "./components/RoomPanel.jsx";
import { RoomsPanel } from "./components/RoomsPanel.jsx";
import { SystemActivity } from "./components/SystemActivity.jsx";
import { useMbgChat } from "./hooks/useMbgChat.js";
import { ROLE_LABELS } from "./utils/uiConstants.js";
import {
  CapIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  InfoCircleIcon,
  LogOutIcon,
  UserCircleIcon,
  XCircleIcon,
  XIcon,
} from "./components/icons/UiIcons.jsx";
import { useEffect, useRef, useState } from "react";

function App() {
  const chat = useMbgChat();
  const role = chat.session?.role || "guest";
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef(null);

  useEffect(() => {
    document.body.dataset.role = role;
    document.body.classList.toggle("is-guest", role === "guest");
  }, [role]);

  useEffect(() => {
    document.title = "Study Room";
  }, []);

  useEffect(() => {
    if (!accountMenuOpen) return undefined;
    function onPointerDown(event) {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target)) {
        setAccountMenuOpen(false);
      }
    }
    function onKeyDown(event) {
      if (event.key === "Escape") setAccountMenuOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [accountMenuOpen]);

  const userPillLabel = chat.session
    ? `${ROLE_LABELS[chat.session.role] || chat.session.role}: ${chat.session.username}`
    : null;

  return (
    <div
      className="w-[min(1680px,calc(100%-32px))] min-h-screen mx-auto py-4 pb-6"
      data-role={role}
    >
      {role === "guest" ? (
        <main
          className="grid min-h-screen place-items-center bg-[radial-gradient(120%_90%_at_50%_-10%,rgba(37,99,235,0.1),transparent_60%),linear-gradient(180deg,#f4f7ff_0%,#e9eefc_48%,#dbe4fb_100%)] px-5 py-8"
          aria-label="Sign in to Study Room"
        >
          <AccessPanel chat={chat} variant="auth" />
        </main>
      ) : (
        <>
          <header className="sticky top-0 z-20 mb-4 w-full border-b border-border bg-white/95 shadow-sm backdrop-blur-[18px]">
            <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-[18px] min-h-[68px] px-5 py-[14px]">
              <div className="flex items-center gap-[14px] min-w-0">
                <span
                  className="inline-flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-[13px] bg-[linear-gradient(150deg,var(--primary),#4f46e5)] text-[1.02rem] font-black tracking-[0.02em] text-white shadow-[0_10px_22px_rgba(37,99,235,0.28)]"
                  aria-hidden="true"
                >
                  MBG
                </span>
                <div className="min-w-0">
                  <p className="m-0 mb-1.5 text-[#b9c8d8] text-[0.72rem] font-black tracking-[0.04em] uppercase">
                    MARI BELAJAR GUYS
                  </p>
                  <h1 className="text-[clamp(1.4rem,2vw,1.85rem)] leading-[1.1]">Study Room</h1>
                  <p className="mt-1 mb-0 text-[var(--muted)] text-[0.82rem] font-semibold">
                    Collaborate, learn, and grow together.
                  </p>
                </div>
              </div>

              <div className="inline-flex items-center gap-2.5 flex-wrap justify-end">
                <span
                  className="inline-flex items-center gap-2 max-w-full min-h-[30px] px-[11px] border border-[rgba(37,99,235,0.2)] rounded-full bg-[#eff6ff] text-[#1e3a8a] overflow-hidden text-[0.78rem] font-black text-ellipsis whitespace-nowrap"
                  role="status"
                >
                  <span
                    className={`w-[9px] h-[9px] shrink-0 rounded-full ${
                      chat.connected
                        ? "bg-green-500 shadow-[0_0_0_4px_rgba(34,197,94,0.16)]"
                        : "bg-danger shadow-[0_0_0_4px_rgba(163,62,49,0.14)]"
                    }`}
                    aria-hidden="true"
                  />
                  <span>{chat.connected ? "Connected" : "Disconnected"}</span>
                </span>

                {userPillLabel && (
                  <div className="relative" ref={accountMenuRef}>
                    <button
                      type="button"
                      className="inline-flex min-h-[44px] cursor-pointer items-center gap-[9px] rounded-full border border-border bg-white py-[5px] pl-[7px] pr-3 text-text shadow-sm transition-[border-color,box-shadow] duration-[140ms] ease hover:border-[rgba(37,99,235,0.4)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                      aria-haspopup="menu"
                      aria-expanded={accountMenuOpen}
                      onClick={() => setAccountMenuOpen((open) => !open)}
                    >
                      <span
                        className="inline-flex items-center justify-center w-[30px] h-[30px] shrink-0 rounded-full bg-[#eff6ff] text-primary"
                        aria-hidden="true"
                      >
                        <UserCircleIcon />
                      </span>
                      <span className="text-[0.84rem] font-extrabold whitespace-nowrap">
                        {userPillLabel}
                      </span>
                      <ChevronDownIcon className="text-[var(--text-muted)] shrink-0" aria-hidden="true" />
                    </button>

                    {accountMenuOpen && (
                      <div
                        className="absolute top-[calc(100%+8px)] right-0 z-40 min-w-[210px] p-2 border border-border rounded-[var(--radius-lg)] bg-white shadow-[0_18px_44px_rgba(15,23,42,0.16)]"
                        role="menu"
                      >
                        <div className="flex items-center gap-[9px] px-[10px] pt-2 pb-[10px] border-b border-border text-[0.84rem] font-extrabold">
                          <span
                            className="inline-flex items-center justify-center w-[30px] h-[30px] shrink-0 rounded-full bg-[#eff6ff] text-primary"
                            aria-hidden="true"
                          >
                            <UserCircleIcon />
                          </span>
                          <span>{userPillLabel}</span>
                        </div>
                        <button
                          type="button"
                          className="flex items-center gap-2.5 w-full mt-1.5 px-[10px] py-[9px] border-0 rounded-[var(--radius-md)] bg-transparent text-danger text-[0.86rem] font-extrabold cursor-pointer text-left hover:bg-danger-bg focus-visible:outline-2 focus-visible:outline-danger focus-visible:outline-offset-2"
                          role="menuitem"
                          onClick={() => {
                            setAccountMenuOpen(false);
                            chat.send("logout");
                          }}
                        >
                          <LogOutIcon aria-hidden="true" />
                          <span>Log Out</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </header>

          <ActionToast notice={chat.actionNotice} onClose={chat.dismissActionNotice} />

          <main
            className="app-body grid grid-cols-1 items-start gap-5 lg:grid-cols-[240px_minmax(0,1fr)] xl:grid-cols-[250px_minmax(620px,1fr)_330px]"
            aria-label="Study Room"
          >
            <aside
              className="sticky top-[104px] grid min-w-0 content-start gap-3"
              aria-label="Navigation"
            >
              <OnlineUsersPanel chat={chat} />
              <RoomsPanel chat={chat} />
            </aside>

            <section className="grid min-w-0 gap-4" aria-label="Discussion Room">
              <MessageCenter chat={chat} />
              {role === "admin" && <SystemActivity chat={chat} />}
            </section>

            <aside
              className="class-panel grid min-w-0 content-start gap-0 overflow-hidden rounded-[var(--radius-lg)] border border-[rgba(15,23,42,0.08)] bg-white/95 pb-2 shadow-sm lg:col-span-2 xl:col-span-1"
              aria-label="Class Panel"
            >
              <div className="flex items-center justify-start gap-3 min-w-0 min-h-14 px-4 py-3.5 border-b border-slate-200 bg-white">
                <span
                  className="inline-flex items-center justify-center shrink-0 w-8 h-8 rounded-[9px] bg-slate-100 text-slate-700"
                  aria-hidden="true"
                >
                  <CapIcon />
                </span>
                <div className="grid gap-[3px] min-w-0">
                  <h2 className="text-[1.05rem] font-extrabold text-text">Class Panel</h2>
                  <span className="text-[var(--text-muted)] text-[0.8rem] font-bold">Manage rooms and members</span>
                </div>
              </div>

              <RoomPanel chat={chat} />
              {role === "admin" && <PendingRequestsPanel chat={chat} />}
              {(role === "admin" || role === "teacher") && <ManageUsersPanel chat={chat} />}
            </aside>
          </main>
        </>
      )}

      <RejectDialog chat={chat} />
    </div>
  );
}

function ActionToast({ notice, onClose }) {
  if (!notice) return null;

  const toneClass = notice.tone === "error"
    ? "action-toast--error"
    : notice.tone === "system"
      ? "action-toast--system"
      : "action-toast--success";
  const Icon = notice.tone === "error"
    ? XCircleIcon
    : notice.tone === "system"
      ? InfoCircleIcon
      : CheckCircleIcon;
  const title = notice.tone === "error"
    ? "Gagal"
    : notice.tone === "system"
      ? "Info"
      : "Berhasil";
  const description = getToastDescription(notice);

  return (
    <div
      className={`action-toast ${toneClass}`}
      role="status"
      aria-live="polite"
    >
      <span className="action-toast-icon" aria-hidden="true">
        <Icon />
      </span>
      <span className="action-toast-copy">
        <strong className="action-toast-title">{title}</strong>
        <span className="action-toast-message">{description}</span>
      </span>
      <button
        type="button"
        className="action-toast-close"
        aria-label="Close notification"
        onClick={onClose}
      >
        <XIcon />
      </button>
      <span className="action-toast-progress" aria-hidden="true" />
    </div>
  );
}

function getToastDescription(notice) {
  const content = String(notice?.content || "").trim();
  if (!content) {
    return notice?.tone === "error" ? "Action failed. Please try again." : "Action completed successfully.";
  }

  return content
    .replace(/_/g, " ")
    .replace(/\s+response\b/gi, "")
    .replace(/\bresponse\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

export default App;
