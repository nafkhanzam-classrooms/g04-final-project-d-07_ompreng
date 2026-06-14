import { displayRoomName, roomNameFor } from "../utils/chatFormat.js";
import { EmptyState, IconBadge, ListRow, Panel, PanelHeading } from "./common.jsx";
import { FolderIcon } from "./icons/UiIcons.jsx";

export function RoomsPanel({ chat }) {
  return (
    <Panel className="side-panel" aria-labelledby="roomsTitle">
      <PanelHeading className="side-panel-heading">
        <IconBadge className="side-panel-icon">
          <FolderIcon />
        </IconBadge>
        <h2 id="roomsTitle" className="text-[0.96rem] font-extrabold text-text">My Rooms</h2>
      </PanelHeading>

      <div
        className="grid max-h-[250px] content-start gap-1.5 overflow-auto p-2.5"
        aria-live="polite"
      >
        {chat.joinedRooms.length ? (
          chat.joinedRooms.map((room) => {
            const roomName = roomNameFor(room);
            const memberCount =
              room.member_count ?? (Array.isArray(room.members) ? room.members.length : 0);
            const description = [
              room.description,
              `${memberCount} member${memberCount === 1 ? "" : "s"}`,
            ]
              .filter(Boolean)
              .join(" / ");
            return (
              <ListRow
                key={roomName}
                title={displayRoomName(roomName)}
                detail={description}
                onClick={() => {
                  chat.selectRoom(roomName);
                  chat.openThread(`room:${roomName}`);
                }}
              />
            );
          })
        ) : (
          <EmptyState
            className="px-3 py-4"
            icon={<FolderIcon width={26} height={26} />}
            title="You haven't joined any rooms yet."
            detail="Pick or request a room to start a discussion."
          />
        )}
      </div>
    </Panel>
  );
}
