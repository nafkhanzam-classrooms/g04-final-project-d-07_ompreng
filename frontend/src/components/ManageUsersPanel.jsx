import { displayRoomName } from "../utils/chatFormat.js";
import { Button, PanelHeading } from "./common.jsx";
import { roleLabel } from "../utils/uiConstants.js";
import { useEffect, useState } from "react";

export function ManageUsersPanel({ chat }) {
  const [target, setTarget] = useState("");

  useEffect(() => {
    if (!chat.moderationTargets.some((user) => user.username === target)) {
      setTarget(chat.moderationTargets[0]?.username || "");
    }
  }, [chat.moderationTargets, target]);

  return (
    <section
      className="admin-section class-panel-section grid bg-surface"
      aria-labelledby="moderationTitle"
    >
      <PanelHeading className="class-panel-heading">
        <h2 id="moderationTitle" className="text-[1.05rem] font-extrabold text-text">
          Manage Members
        </h2>
      </PanelHeading>

      <div className="control-section form-grid grid grid-cols-1 gap-3 px-4 py-3.5 md:grid-cols-[repeat(2,minmax(0,1fr))]">
        <label>
          <span>Room</span>
          <select
            value={chat.selectedRoom}
            onChange={(event) => chat.selectRoom(event.target.value)}
          >
            <option value="" disabled>Use selected room</option>
            {chat.joinedRoomOptions.map((roomName) => (
              <option key={roomName} value={roomName}>{displayRoomName(roomName)}</option>
            ))}
          </select>
        </label>
        <label>
          <span>User</span>
          <select value={target} onChange={(event) => setTarget(event.target.value)}>
            <option value="" disabled>Choose a user</option>
            {chat.moderationTargets.map((user) => (
              <option key={user.username} value={user.username}>
                {user.username} / {roleLabel(user.role)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="button-grid grid grid-cols-[repeat(auto-fit,minmax(132px,1fr))] gap-2.5 px-4 pb-4">
        <Button
          variant="danger-outline"
          disabled={!chat.selectedRoom || !target || chat.isActionPending("kick_user")}
          onClick={() =>
            chat.send("kick_user", {
              room_name: chat.selectedRoom,
              target_username: target,
            })
          }
        >
          {chat.isActionPending("kick_user") ? "Removing..." : "Remove User"}
        </Button>
      </div>
    </section>
  );
}
