def parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], dict[str, tuple[str, str, bytes]]]:
    marker = "boundary="
    if marker not in content_type:
        return {}, {}
    boundary = content_type.split(marker, 1)[1].strip().strip('"')
    boundary_bytes = ("--" + boundary).encode("utf-8")
    fields = {}
    files = {}
    for raw_part in body.split(boundary_bytes):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        if part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")
        if b"\r\n\r\n" not in part:
            continue
        raw_headers, content = part.split(b"\r\n\r\n", 1)
        part_headers = {}
        for line in raw_headers.decode("iso-8859-1").split("\r\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                part_headers[key.strip().lower()] = value.strip()
        params = parse_header_params(part_headers.get("content-disposition", ""))
        name = params.get("name", "")
        filename = params.get("filename")
        if filename:
            files[name] = (filename, part_headers.get("content-type", "application/octet-stream"), content)
        elif name:
            fields[name] = content.decode("utf-8", errors="replace")
    return fields, files

def parse_header_params(value: str) -> dict[str, str]:
    params = {}
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if "=" in chunk:
            key, raw_value = chunk.split("=", 1)
            params[key.strip().lower()] = raw_value.strip().strip('"')
    return params
