import { useEffect, useRef, useState } from "react";
import { formatDisplayText, formatFileSize, reactionChoices } from "../utils/chatFormat.js";
import { Button, EmptyState } from "./common.jsx";
import { reactionConfig } from "./icons/ReactionIcons.jsx";
import { roleLabel } from "../utils/uiConstants.js";
import {
  BellIcon,
  ChatIcon,
  CheckCircleIcon,
  TrashIcon,
  UsersIcon,
  UserCircleIcon,
} from "./icons/UiIcons.jsx";

export function MessageCenter({ chat }) {
  const [content, setContent] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [directTarget, setDirectTarget] = useState("");
  const [announceContent, setAnnounceContent] = useState("");
  const fileInputRef = useRef(null);
  const messagesRef = useRef(null);
  const isNotifications = chat.activeMode === "notifications";
  const isRoom = chat.activeMode === "room";
  const isDirect = chat.activeMode === "direct";
  const isAdmin = chat.session?.role === "admin";
  const messageSendPending =
    chat.isActionPending("send_room_message")
    || chat.isActionPending("send_private_message")
    || chat.isActionPending("send_file_message");

  const contextTitle = isDirect
    ? `Private Message with @${chat.activeThreadKey.slice(3)}`
    : isRoom
      ? chat.activeThread?.label
      : "Discussion Room";
  const contextSubtitle = isDirect
    ? "Private conversation between users."
    : isRoom
      ? "Discussion with room members."
      : "Stay updated with room activities and important announcements.";

  useEffect(() => {
    if (isDirect) setDirectTarget(chat.activeThreadKey.slice(3));
  }, [chat.activeThreadKey, isDirect]);

  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight });
  }, [chat.activeThread?.items?.length]);

  async function sendMessage() {
    const sent = await chat.sendComposerMessage({ content, attachment, target: directTarget });
    if (sent) {
      setContent("");
      setAttachment(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function clearFile() {
    setAttachment(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function sendGlobalAnnouncement() {
    if (!announceContent.trim()) return;
    if (chat.globalAnnounce(announceContent)) {
      setAnnounceContent("");
    }
  }

  return (
    <section
      className="panel feed-panel activity-panel grid min-h-[720px] grid-rows-[auto_minmax(0,1fr)_auto] border-slate-900/10 shadow-sm"
      aria-labelledby="feedTitle"
    >
      <div className="panel-heading min-h-[66px] px-5 py-3.5 bg-white">
        <span
          className="inline-flex items-center justify-center shrink-0 w-9 h-9 rounded-[10px] bg-slate-100 text-slate-700 [&_svg]:w-5 [&_svg]:h-5"
          aria-hidden="true"
        >
          <ChatIcon />
        </span>
        <div className="grid gap-[3px] min-w-0">
          <h2 id="feedTitle" className="text-[1.18rem] font-black text-text">{contextTitle}</h2>
          <span className="text-[var(--text-muted)] text-[0.8rem] font-bold">{contextSubtitle}</span>
        </div>
        <Button
          variant="danger-outline"
          className="ml-auto inline-flex min-h-8 items-center gap-[7px] rounded-[var(--radius-md)] px-2.5 text-[0.76rem]"
          aria-label="Clear all messages in the current view"
          title="Clear All"
          onClick={chat.clearActiveThread}
        >
          <TrashIcon aria-hidden="true" />
          <span>Clear All</span>
        </Button>
      </div>

      <div className="message-center grid min-h-[500px] min-w-0 grid-cols-1 lg:grid-cols-[minmax(190px,230px)_minmax(0,1fr)]">
        <ThreadSidebar chat={chat} />
        <div
          className="messages flex flex-col min-w-0 min-h-0 h-[500px] gap-2.5 overflow-auto bg-[#f8fafc] px-4 py-4"
          aria-label="Message list"
          aria-live="polite"
          ref={messagesRef}
        >
          {chat.activeThread?.items?.length ? (
            chat.activeThread.items.map((entry) => (
              <MessageItem key={entry.id} entry={entry} chat={chat} activeMode={chat.activeMode} />
            ))
          ) : (
            <EmptyState>
              <strong>No messages yet.</strong>
              <span>Start a discussion or pick a room first.</span>
            </EmptyState>
          )}
        </div>
      </div>

      {isAdmin && isNotifications && (
        <div className="sticky bottom-0 z-[2] grid gap-3 min-w-0 p-[14px] border-t-2 border-primary bg-[#f0f5ff]">
          <p className="m-0 text-[var(--muted)] text-[0.72rem] font-[950] tracking-[0.06em] uppercase">
            Global Announcement
          </p>
          <p className="m-0 text-[0.82rem] text-text">
            This announcement will appear in every user&apos;s Notifications.
          </p>
          <label className="col-span-full">
            <span>Announcement</span>
            <textarea
              value={announceContent}
              onChange={(event) => setAnnounceContent(event.target.value)}
              rows="3"
              placeholder="Type an announcement for all users..."
            />
          </label>
          <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2.5">
            <Button
              variant="primary"
              disabled={!announceContent.trim() || chat.isActionPending("send_global_announcement")}
              onClick={sendGlobalAnnouncement}
            >
              {chat.isActionPending("send_global_announcement") ? "Sending..." : "Send Global Announcement"}
            </Button>
          </div>
        </div>
      )}

      {!isNotifications && (
        <div className="conversation-composer sticky bottom-0 z-[2] grid min-w-0 gap-2.5 border-t border-slate-200 bg-white/95 px-4 py-3">
          {isDirect && (
            <label className="grid gap-1.5 rounded-[8px] bg-slate-50 p-2">
              <span>Target User</span>
              <select
                value={directTarget}
                onChange={(event) => setDirectTarget(event.target.value)}
              >
                <option value="" disabled>Choose an online user</option>
                {chat.onlineTargets.map((user) => (
                  <option key={user.username} value={user.username}>
                    {user.username} / {roleLabel(user.role)}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="attachment-picker grid min-w-0 grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2">
            <label
              className="attachment-button inline-flex min-h-[32px] items-center justify-center rounded-[7px] border border-slate-200 bg-white px-2.5 text-[0.78rem] font-extrabold text-slate-700 cursor-pointer"
              htmlFor="attachmentInput"
            >
              Attach
            </label>
            <input
              id="attachmentInput"
              ref={fileInputRef}
              type="file"
              className="absolute w-px h-px opacity-0 pointer-events-none"
              onChange={(event) => setAttachment(event.target.files?.[0] || null)}
            />
            <span className="min-w-0 overflow-hidden text-[var(--muted)] text-[0.78rem] font-bold text-ellipsis whitespace-nowrap">
              {attachment
                ? `${attachment.name} / ${formatFileSize(attachment.size)}`
                : "No file selected"}
            </span>
            {attachment && (
              <button
                type="button"
                className="inline-flex min-h-8 shrink-0 items-center justify-center rounded-[7px] border border-slate-200 bg-white px-2.5 text-[0.76rem] font-extrabold text-slate-600 hover:border-danger/25 hover:bg-danger-bg hover:text-danger focus-visible:outline-2 focus-visible:outline-danger focus-visible:outline-offset-2"
                aria-label="Remove selected file"
                onClick={clearFile}
              >
                Remove file
              </button>
            )}
          </div>

          <div className="composer-input-row grid min-w-0 gap-2">
            <label className="min-w-0">
              <span className="sr-only">Message</span>
              <textarea
                value={content}
                onChange={(event) => setContent(event.target.value)}
                rows="4"
                placeholder={isDirect ? "Type a private message" : "Type a message for the room"}
              />
            </label>
            <div className="flex justify-end">
              <Button
                variant="primary"
                className="send-button min-h-[44px] px-5"
                disabled={messageSendPending}
                onClick={sendMessage}
              >
                {messageSendPending ? "Sending..." : "Send"}
              </Button>
            </div>
          </div>

          {isRoom && chat.session?.role !== "student" && (
            <div className="flex justify-end">
              <Button
                variant="secondary"
                className="min-h-8 px-2.5 py-1.5 text-[0.76rem]"
                disabled={chat.isActionPending("send_announcement")}
                onClick={() => chat.announce(content) && setContent("")}
              >
                {chat.isActionPending("send_announcement") ? "Announcing..." : "Room Announcement"}
              </Button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function ThreadSidebar({ chat }) {
  const sections = [
    ["rooms", "Rooms", ChatIcon],
    ["direct", "Private Messages", UsersIcon],
    ["notifications", "Notifications", BellIcon],
  ];
  const threads = Object.values(chat.threads).sort((a, b) => a.label.localeCompare(b.label));

  return (
    <aside
      className="grid content-start min-w-0 gap-2 overflow-auto p-4 pr-[14px] border-r border-border bg-[#fbfcfe] text-[var(--ink)]"
      aria-label="Message navigation"
    >
      {sections.map(([section, title, Icon]) => {
        const sectionThreads = threads.filter((thread) => thread.section === section);
        const sectionActive = sectionThreads.some(
          (thread) => thread.key === chat.activeThreadKey,
        );
        const primary = sectionThreads[0];
        return (
          <section className="grid gap-[7px]" data-thread-section={section} key={section}>
            <button
              type="button"
              className={`thread-nav-item ${sectionActive ? "active" : ""}`.trim()}
              onClick={() => primary && chat.openThread(primary.key)}
              disabled={!primary}
            >
              <Icon aria-hidden="true" />
              <span>{title}</span>
            </button>
            {sectionThreads.length > 0 && (
              <div className="grid gap-1.5 pl-[38px]">
                {sectionThreads.map((thread) => (
                  <button
                    key={thread.key}
                    className={`thread-button ${thread.key === chat.activeThreadKey ? "active" : ""}`}
                    type="button"
                    onClick={() => chat.openThread(thread.key)}
                  >
                    {thread.label}
                  </button>
                ))}
              </div>
            )}
          </section>
        );
      })}
    </aside>
  );
}

function MessageItem({ entry, chat, activeMode }) {
  const reactions = Array.isArray(entry.reactions) ? entry.reactions : [];
  const metaParts = String(entry.meta || "").split(" / ").filter(Boolean);
  const timestamp = metaParts.length > 1 ? metaParts.at(-1) : "";
  const meta = timestamp ? metaParts.slice(0, -1).join(" / ") : entry.meta;
  const sender = timestamp ? metaParts.at(-2) : "";
  const isMine = activeMode !== "notifications" && sender === chat.session?.username;
  const isSuccess = entry.tone === "success";
  const canReact = entry.messageId && entry.canReact && !entry.deleted && activeMode !== "notifications";
  const LeadingIcon = isSuccess ? CheckCircleIcon : UserCircleIcon;

  const toneClasses = {
    success: "message-bubble-success",
    error: "message-bubble-error",
    system: "message-bubble-system",
    private: "message-bubble-private",
    announcement: "message-bubble-announcement",
    deleted: "message-bubble-deleted",
    normal: "message-bubble-normal",
  };
  const tone = entry.tone || "normal";
  const extraToneClass = toneClasses[tone] || toneClasses.normal;

  return (
    <article
      className={`message-row flex w-full ${isMine ? "justify-end" : "justify-start"}`.trim()}
      data-message-id={entry.messageId || undefined}
    >
      <div className={`message-bubble ${extraToneClass} ${isMine ? "message-bubble-mine" : ""}`.trim()}>
        {!isMine && (
          <span
            className={`message-avatar ${isSuccess ? "text-success" : "text-slate-500"}`}
            aria-hidden="true"
          >
            <LeadingIcon />
          </span>
        )}
        {entry.meta && (
          <span className="message-meta">
            <span className="message-meta-main">
              {formatDisplayText(meta)}
            </span>
            {timestamp && (
              <time className="message-time">{timestamp}</time>
            )}
          </span>
        )}
        <div className={`message-content whitespace-pre-wrap ${tone === "error" ? "text-danger" : ""}`}>
          {formatDisplayText(entry.content || "-")}
        </div>
        {entry.attachment && <Attachment attachment={entry.attachment} />}

        {canReact && (
          <div className="reaction-strip">
            {reactionChoices.map((emoji) => {
              const reaction = reactions.find((item) => item.emoji === emoji);
              const count = reaction?.count || 0;
              const config = reactionConfig[emoji] || { label: emoji, Icon: null };
              const { label, Icon } = config;
              return (
                <button
                  key={emoji}
                  type="button"
                  className={`reaction-chip ${count ? "active" : ""}`.trim()}
                  data-reaction={emoji}
                  title={count ? `${label} (${count})` : label}
                  aria-label={`${label}${count ? ` (${count})` : ""}`}
                  onClick={() =>
                    chat.send("toggle_reaction", { message_id: entry.messageId, emoji })
                  }
                >
                  {Icon && <Icon className="reaction-icon" />}
                  <span>{count || label}</span>
                </button>
              );
            })}
          </div>
        )}

        {chat.session?.role === "admin" &&
          entry.messageId &&
          entry.canDelete &&
          !entry.deleted && (
            <div className="flex justify-end gap-2 mt-2">
              <button
                type="button"
                className="inline-flex items-center justify-center w-[30px] h-[30px] border border-danger rounded-[var(--radius-sm)] bg-danger-bg text-danger cursor-pointer transition-[background] duration-[140ms] hover:bg-danger hover:text-white focus-visible:outline-2 focus-visible:outline-danger focus-visible:outline-offset-2"
                aria-label="Delete this message for everyone"
                disabled={chat.isActionPending("delete_message")}
                onClick={() =>
                  window.confirm("Delete this message for everyone?") &&
                  chat.send("delete_message", { message_id: entry.messageId })
                }
              >
                <TrashIcon />
              </button>
            </div>
          )}
      </div>
    </article>
  );
}

function Attachment({ attachment }) {
  return (
    <div className="mt-2 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2.5 rounded-[var(--radius-md)] border border-[rgba(101,115,109,0.24)] bg-[var(--surface-muted)] p-2">
      <div className="min-w-0">
        <strong className="block overflow-hidden text-ellipsis whitespace-nowrap">
          {attachment.original_name || "attachment"}
        </strong>
        <span className="block overflow-hidden text-ellipsis whitespace-nowrap text-[var(--muted)] text-[0.75rem] font-[850]">
          {formatFileSize(attachment.size || 0)}
        </span>
      </div>
      <a
        className="attachment-download text-[var(--accent)] text-[0.8rem] font-[950] no-underline focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
        href={attachment.download_url || "#"}
        download={attachment.original_name || ""}
      >
        Download
      </a>
    </div>
  );
}
