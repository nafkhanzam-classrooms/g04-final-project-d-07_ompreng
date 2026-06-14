import { useState } from "react";
import { displayRoomName, roomNameFor } from "../utils/chatFormat.js";
import { Button, PanelHeading, Pill } from "./common.jsx";

export function RoomPanel({ chat }) {
  const [newRoomName, setNewRoomName] = useState("");
  const [description, setDescription] = useState("");
  const [purpose, setPurpose] = useState("");
  const role = chat.session?.role;
  const selectedRoomLabel = displayRoomName(chat.selectedRoom) || "No room selected";
  const selectedRoom = chat.rooms.find((room) => roomNameFor(room) === chat.selectedRoom);
  const isSelectedRoomMember = Boolean(chat.session?.username && selectedRoom?.members?.includes(chat.session.username));
  const requestedRoomPending = chat.hasPendingRoomRequest(newRoomName);
  const requestRoomDisabled =
    !newRoomName.trim() || requestedRoomPending || chat.isActionPending("request_room");

  function roomPayload(extra = {}) {
    return { room_name: newRoomName.trim(), description: description.trim(), ...extra };
  }

  const createLabel = role === "admin" ? "Create Room" : "Request Room";

  return (
    <section
      className="admin-section class-panel-section grid bg-surface"
      aria-labelledby="roomOpsTitle"
    >
      <PanelHeading className="class-panel-heading">
        <h2 id="roomOpsTitle" className="text-[1.05rem] font-extrabold text-text">Active Room</h2>
        <Pill className="ml-auto max-w-full gap-2 overflow-hidden text-ellipsis whitespace-nowrap border border-slate-900/10 bg-white px-[11px] text-[0.78rem] text-text-muted">
          {displayRoomName(chat.selectedRoom) || "No room"}
        </Pill>
      </PanelHeading>

      <div className="control-section selected-room-panel grid gap-3 px-4 py-3.5">
        <label>
          <span>Select Room</span>
          <select
            value={chat.selectedRoom}
            onChange={(event) => chat.selectRoom(event.target.value)}
          >
            <option value="" disabled>Select Room</option>
            {chat.roomOptions.map((roomName) => (
              <option key={roomName} value={roomName}>{displayRoomName(roomName)}</option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-[repeat(auto-fit,minmax(92px,1fr))] gap-2.5">
          <Button
            variant="primary"
            className="min-w-0 px-2 text-center text-[0.82rem]"
            aria-label="Join room"
            disabled={!chat.selectedRoom || isSelectedRoomMember || chat.isActionPending("join_room")}
            onClick={() => chat.send("join_room", { room_name: chat.selectedRoom })}
          >
            {chat.isActionPending("join_room") ? "Joining..." : isSelectedRoomMember ? "Joined" : "Join"}
          </Button>
          <Button
            variant="danger-outline"
            className="min-w-0 px-2 text-center text-[0.82rem]"
            aria-label="Leave room"
            disabled={!chat.selectedRoom || !isSelectedRoomMember || chat.isActionPending("leave_room")}
            onClick={() => chat.send("leave_room", { room_name: chat.selectedRoom })}
          >
            {chat.isActionPending("leave_room") ? "Leaving..." : "Leave Room"}
          </Button>
        </div>

        {role === "admin" && (
          <Button
            variant="danger"
            className="w-full text-center text-[0.82rem]"
            aria-label={`Delete ${selectedRoomLabel}`}
            disabled={!chat.selectedRoom || chat.isActionPending("delete_room")}
            onClick={() => chat.send("delete_room", { room_name: chat.selectedRoom })}
          >
            {chat.isActionPending("delete_room") ? "Deleting..." : "Delete Room"}
          </Button>
        )}
      </div>

      <div className="control-section grid px-4 py-3.5">
        <div>
          <h3 className="control-section-title">Create/Request Room</h3>
        </div>
        <div className="form-grid grid grid-cols-1 gap-3 pt-3 md:grid-cols-[repeat(2,minmax(0,1fr))]">
          <label>
            <span>Room Name</span>
            <input
              value={newRoomName}
              onChange={(event) => setNewRoomName(event.target.value)}
              placeholder="e.g. progjar"
              autoComplete="off"
            />
          </label>
          <label>
            <span>Description</span>
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="e.g. Assignment discussion"
              autoComplete="off"
            />
          </label>
          {role !== "admin" && (
            <label className="col-span-full">
              <span>Room Purpose</span>
              <input
                value={purpose}
                onChange={(event) => setPurpose(event.target.value)}
                placeholder="e.g. Group study"
                autoComplete="off"
              />
            </label>
          )}
        </div>
        <div className="button-grid grid grid-cols-[repeat(auto-fit,minmax(132px,1fr))] gap-2.5 pt-3">
          {role === "admin" ? (
            <Button
              variant="primary"
              disabled={!newRoomName.trim() || chat.isActionPending("create_room")}
              onClick={() => chat.send("create_room", roomPayload())}
            >
              {chat.isActionPending("create_room") ? "Creating..." : createLabel}
            </Button>
          ) : (
            <Button
              variant="primary"
              disabled={requestRoomDisabled}
              onClick={() =>
                chat.send("request_room", roomPayload({ purpose: purpose.trim() }))
              }
            >
              {chat.isActionPending("request_room")
                ? "Requesting..."
                : requestedRoomPending
                  ? "Request Pending"
                  : createLabel}
            </Button>
          )}
        </div>
      </div>

    </section>
  );
}
