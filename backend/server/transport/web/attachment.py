import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse
from backend.server.services.message import MessageService
from backend.server.transport.web.multipart import parse_multipart

def serve_attachment(target: str, database_path: str, upload_dir: str, send_response_func: any) -> None:
    parsed = urlparse(target)
    attachment_id = unquote(parsed.path.rsplit("/", 1)[-1])
    params = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
    token = unquote(params.get("token", ""))
    service = MessageService(database_path=database_path, upload_dir=upload_dir)
    success, message, code, attachment = service.attachment_download(attachment_id, token)
    if not success:
        status = 404 if code == "ATTACHMENT_NOT_FOUND" else 403
        send_response_func(status, message.encode("utf-8"), "text/plain")
        return
    path = Path(attachment["path"])
    content_type = attachment.get("mime_type") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    send_response_func(200, path.read_bytes(), content_type)

def handle_attachment_upload(headers: dict[str, str], body: bytes, database_path: str, upload_dir: str, send_json_response_func: any) -> None:
    content_type = headers.get("content-type", "")
    if not content_type.lower().startswith("multipart/form-data"):
        send_json_response_func(400, {"success": False, "message": "Attachment upload must use multipart/form-data", "payload": {"code": "INVALID_CONTENT_TYPE"}})
        return
    fields, files = parse_multipart(content_type, body)
    upload_token = fields.get("upload_token", "")
    uploaded_file = files.get("file")
    if not upload_token or uploaded_file is None:
        send_json_response_func(400, {"success": False, "message": "Upload token and file are required", "payload": {"code": "VALIDATION_ERROR"}})
        return

    file_name, mime_type, raw_bytes = uploaded_file
    service = MessageService(database_path=database_path, upload_dir=upload_dir)
    success, message, code, attachment = service.save_uploaded_attachment(upload_token, file_name, mime_type, raw_bytes)
    if not success:
        status = 404 if code == "UPLOAD_TICKET_NOT_FOUND" else 400
        send_json_response_func(status, {"success": False, "message": message, "payload": {"code": code}})
        return
    send_json_response_func(200, {"success": True, "message": message, **(attachment or {})})
