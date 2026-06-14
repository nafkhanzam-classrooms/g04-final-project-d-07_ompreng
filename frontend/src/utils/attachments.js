export async function uploadPreparedAttachment(file, uploadToken) {
  const form = new FormData();
  form.append("upload_token", uploadToken);
  form.append("file", file, file.name);
  const response = await fetch("/attachments", { method: "POST", body: form });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.success === false) {
    throw new Error(payload.message || "File upload failed");
  }
  return payload;
}
