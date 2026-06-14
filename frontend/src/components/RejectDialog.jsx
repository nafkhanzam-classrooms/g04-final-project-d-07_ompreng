import { useEffect, useRef, useState } from "react";
import { Button } from "./common.jsx";

export function RejectDialog({ chat }) {
  const dialogRef = useRef(null);
  const [reason, setReason] = useState("");
  const request = chat.pendingRejectRequest;
  const id = request?.id ?? request?.request_id ?? "";
  const rejectPending = chat.isActionPending("reject_room_request");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (request && !dialog.open) {
      setReason("");
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    if (!request && dialog.open) dialog.close();
  }, [request]);

  function close() {
    chat.setPendingRejectRequest(null);
  }

  function confirmReject() {
    if (!request || !reason.trim()) return;
    chat.send("reject_room_request", { request_id: id, reason: reason.trim() });
    close();
  }

  return (
    <dialog
      className="modal-dialog w-[min(460px,calc(100%-28px))] border-0 rounded-[8px] p-0 bg-transparent backdrop:bg-[rgba(15,23,42,0.58)]"
      ref={dialogRef}
      onClose={close}
    >
      <form
        method="dialog"
        className="overflow-hidden border border-[var(--line)] rounded-[8px] bg-surface shadow-[var(--shadow)]"
      >
        <div className="panel-heading">
          <h2 className="text-[1.05rem] font-extrabold text-text">Reject Request #{id}</h2>
        </div>

        <div className="grid gap-[13px] p-4">
          <p className="m-0 text-[var(--muted)] leading-[1.45]">
            {[request?.room_name, request?.requested_by, request?.purpose || request?.description]
              .filter(Boolean)
              .join(" / ")}
          </p>
          <label>
            <span>Rejection Reason</span>
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows="4"
              placeholder="Write the rejection reason"
              required
            />
          </label>

          <div className="flex gap-2.5 pt-3">
            <Button variant="primary" className="flex-1" onClick={close}>Cancel</Button>
            <Button
              variant="danger"
              className="flex-1"
              disabled={!reason.trim() || rejectPending}
              onClick={confirmReject}
            >
              {rejectPending ? "Rejecting..." : "Reject"}
            </Button>
          </div>
        </div>
      </form>
    </dialog>
  );
}
