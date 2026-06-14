import { displayRoomName } from "../utils/chatFormat.js";
import { Button, EmptyState, ListRow, PanelHeading } from "./common.jsx";
import { InboxIcon } from "./icons/UiIcons.jsx";

export function PendingRequestsPanel({ chat }) {
  return (
    <section
      className="admin-section class-panel-section grid bg-surface"
      aria-labelledby="requestOpsTitle"
    >
      <PanelHeading className="class-panel-heading">
        <h2 id="requestOpsTitle" className="text-[1.05rem] font-extrabold text-text">
          Pending Requests
        </h2>
      </PanelHeading>

      <div
        className="grid max-h-[220px] content-start gap-2 overflow-auto px-3 py-3"
        aria-live="polite"
      >
        {chat.pendingRequests.length ? (
          chat.pendingRequests.map((request) => {
            const id = request.id ?? request.request_id ?? "";
            const roomName = request.room_name || request.name || "-";
            const detail = [
              request.requested_by,
              request.requester_role,
              request.purpose || request.description,
            ]
              .filter(Boolean)
              .join(" / ");
            return (
              <ListRow
                key={id}
                title={`#${id} ${displayRoomName(roomName)}`}
                detail={detail}
                onClick={() => chat.selectRoom(roomName)}
                actions={
                  <>
                    <Button
                      variant="primary"
                      className="min-h-[30px] px-2.5 text-[0.74rem]"
                      disabled={chat.isActionPending("approve_room_request")}
                      onClick={() => chat.send("approve_room_request", { request_id: id })}
                    >
                      {chat.isActionPending("approve_room_request") ? "Approving..." : "Approve"}
                    </Button>
                    <Button
                      variant="danger-outline"
                      className="min-h-[30px] px-2.5 text-[0.74rem]"
                      disabled={chat.isActionPending("reject_room_request")}
                      onClick={() => chat.setPendingRejectRequest(request)}
                    >
                      Reject
                    </Button>
                  </>
                }
              />
            );
          })
        ) : (
          <EmptyState
            className="px-3 py-4"
            icon={<InboxIcon width={24} height={24} />}
            title="No pending requests."
          />
        )}
      </div>
    </section>
  );
}
