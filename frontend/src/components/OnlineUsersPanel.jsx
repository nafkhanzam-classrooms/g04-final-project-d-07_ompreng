import { roleLabel } from "../utils/uiConstants.js";
import { EmptyState, IconBadge, ListRow, Panel, PanelHeading, Pill } from "./common.jsx";
import { UsersIcon, UserCircleIcon } from "./icons/UiIcons.jsx";

export function OnlineUsersPanel({ chat }) {
  const onlineCount = (chat.currentUser ? 1 : 0) + chat.onlineTargets.length;

  return (
    <Panel className="side-panel" aria-labelledby="usersTitle">
      <PanelHeading className="side-panel-heading">
        <IconBadge className="side-panel-icon">
          <UsersIcon />
        </IconBadge>
        <h2 id="usersTitle" className="text-[0.96rem] font-extrabold text-text">Online Users</h2>
        <Pill className="ml-auto bg-slate-100 px-[9px] text-[0.68rem] text-slate-700">
          {onlineCount} online
        </Pill>
      </PanelHeading>

      <div className="grid">
        <p className="m-0 px-3 pb-0 pt-3 text-[0.72rem] font-black uppercase tracking-[0.04em] text-slate-500">You</p>
        <div className="grid content-start gap-2 overflow-auto p-2.5" aria-live="polite">
          {chat.currentUser ? (
            <div className="flex min-h-[42px] items-center gap-2.5 rounded-[var(--radius-md)] bg-slate-50 p-2">
              <IconBadge size="md">
                <UserCircleIcon />
              </IconBadge>
              <div className="row-main">
                <strong>{chat.currentUser.username}</strong>
                <span>{roleLabel(chat.currentUser.role)} / you</span>
              </div>
              <Pill className="bg-white text-success">Online</Pill>
            </div>
          ) : (
            <EmptyState className="py-3">Sign in to see your status.</EmptyState>
          )}
        </div>
      </div>

      <div className="grid border-b-0">
        <p className="m-0 px-3 pb-0 pt-2 text-[0.72rem] font-black uppercase tracking-[0.04em] text-slate-500">Other users</p>
        <div
          className="grid max-h-[190px] content-start gap-1.5 overflow-auto p-2.5"
          aria-live="polite"
        >
          {chat.onlineTargets.length ? (
            chat.onlineTargets.map((user) => (
              <ListRow
                key={user.username}
                title={user.username}
                detail={roleLabel(user.role)}
                className="hover:-translate-y-px hover:border-[rgba(49,95,159,0.48)] hover:bg-[#edf3fb] focus-within:border-[rgba(49,95,159,0.48)] focus-within:bg-[#edf3fb]"
                titleText={`Send a private message to ${user.username}`}
                leading={
                  <IconBadge size="md">
                    <UserCircleIcon />
                  </IconBadge>
                }
                onClick={() => {
                  chat.startDirectMessage(user.username);
                  chat.openThread(`dm:${user.username}`);
                }}
                actions={
                  <Pill
                    className="border border-primary/30 bg-[#edf3fb] text-[#4f46e5] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    aria-label={`Send a private message to ${user.username}`}
                  >
                    Message
                  </Pill>
                }
              />
            ))
          ) : (
            <EmptyState
              className="px-3 py-4"
              icon={<UsersIcon width={26} height={26} />}
              title="No other users online yet."
              detail="Invite classmates or teachers to get started."
            />
          )}
        </div>
      </div>
    </Panel>
  );
}
