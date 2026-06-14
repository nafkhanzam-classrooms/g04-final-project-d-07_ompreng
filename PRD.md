# Product Requirements Document

# MBG - Mari Belajar Guys

## Platform Diskusi Akademik Real-Time Berbasis Role dan Multi-Channel

## 1. Overview

MBG, short for Mari Belajar Guys, is a client-server academic discussion platform for real-time communication between Admin, Pengajar, and Pelajar. The system provides managed discussion rooms, role-based access control, chat, private messages, announcements, room request approval, activity logs, and conversation history.

The product follows the SKPL direction: users access MBG through a web browser as the client, while the server handles authentication, authorization, room management, real-time communication, and data persistence. HTTP is used for regular application requests such as login, room management, and history retrieval. WebSocket or socket-based real-time communication is used for live chat events and server push notifications.

## 2. Product Goals

1. Implement a client-server network programming project for Program Jaringan.
2. Build a real-time academic communication platform for Pengajar and Pelajar.
3. Provide structured room management for class discussions and group discussions.
4. Apply role-based access control for Admin, Pengajar, and Pelajar.
5. Support many connected users at the same time.
6. Support multi-channel communication through multiple rooms.
7. Support room messages, private messages, and announcements.
8. Provide room request, approval, rejection, creation, deletion, and moderation flows.
9. Store user data, room data, chat history, and activity logs in a database.
10. Keep the application understandable, demonstrable, and aligned with the SKPL.

## 3. Scope

## 3.1 In Scope

1. Web browser client for Admin, Pengajar, and Pelajar.
2. Server-side authentication and session management.
3. Role-based privilege enforcement.
4. Online user tracking.
5. Room list and room membership.
6. Room creation request workflow.
7. Admin approval and rejection of room requests.
8. Admin direct room creation.
9. Room deletion by Admin.
10. Joining and leaving rooms.
11. Real-time room chat.
12. Private messaging.
13. Pengajar announcements.
14. Kick user moderation.
15. Chat history.
16. Server activity logs.
17. JSON serialization for client-server data exchange.
18. Database persistence for users, rooms, requests, messages, and logs.

## 3.2 Out of Scope for MVP

1. Voice or video calls.
2. File transfer.
3. End-to-end encryption.
4. Mobile native applications.
5. Payment or subscription features.
6. Advanced analytics dashboard.
7. Full production-grade deployment hardening.

## 4. Users and Roles

MBG uses Role-Based Access Control (RBAC). Each user receives permissions based on one of three roles: Admin, Pengajar, or Pelajar.

## 4.1 Admin

Admin is the highest-privilege user and manages overall system activity. Admin can:

1. Login to the system.
2. View online users.
3. View all available rooms.
4. View pending room creation requests.
5. Approve room creation requests.
6. Reject room creation requests.
7. Create rooms directly.
8. Delete rooms.
9. Kick users from rooms when needed.
10. View server activity logs.
11. Send room messages.
12. Send private messages.
13. View chat history.

## 4.2 Pengajar

Pengajar manages learning discussions and class rooms, with privileges below Admin but above Pelajar. Pengajar can:

1. Login to the system.
2. Submit class room creation requests.
3. View available rooms.
4. Join rooms.
5. Leave rooms.
6. Send room messages.
7. Send announcements to room members.
8. Send private messages to Pelajar.
9. View room chat history.
10. Kick Pelajar from rooms managed by the Pengajar.

Pengajar cannot approve room requests, reject room requests, delete arbitrary rooms, or view server logs unless granted Admin privileges.

## 4.3 Pelajar

Pelajar participates in learning and group discussion activities. Pelajar can:

1. Login to the system.
2. View available rooms.
3. Join rooms.
4. Leave rooms.
5. Send and receive room messages.
6. Send and receive private messages.
7. View chat history.
8. Submit group discussion room creation requests.

Pelajar cannot create rooms directly, approve requests, reject requests, delete rooms, view server logs, send announcements, or kick users.

## 5. Core User Stories

1. As an Admin, I want to review room creation requests so that rooms remain organized and appropriate.
2. As an Admin, I want to create or delete rooms directly so that I can manage the system quickly.
3. As an Admin, I want to view server logs so that I can monitor important activity.
4. As a Pengajar, I want to request a class room so that learning discussions can happen in a dedicated space.
5. As a Pengajar, I want to send announcements so that all room members receive important information.
6. As a Pengajar, I want to kick Pelajar from rooms I manage so that discussions remain orderly.
7. As a Pelajar, I want to request a group discussion room so that I can collaborate with classmates.
8. As a Pelajar, I want to join available rooms so that I can participate in discussions.
9. As any authenticated user, I want to send room messages in real time so that discussion feels immediate.
10. As any authenticated user, I want to send private messages so that I can communicate directly with another user.
11. As any authenticated user, I want to view chat history so that I can read earlier discussion context.

## 6. Architecture Requirements

## 6.1 Client-Server Architecture

MBG must use a client-server architecture:

1. The client is accessed through a web browser.
2. The server is the central authority for authentication, authorization, room state, messages, and persistence.
3. The client must not decide user permissions locally.
4. The client sends requests to the server for login, room operations, and history retrieval.
5. The server pushes real-time chat and notification events to connected clients.
6. The database stores users, rooms, room requests, room membership, messages, and logs.

## 6.2 TCP/IP Layer Mapping

| Layer TCP/IP | Protocol Used | Function |
| --- | --- | --- |
| Application Layer | HTTP, WebSocket | Login, data management, and real-time chat communication |
| Transport Layer | TCP | Reliable ordered data delivery |
| Internet Layer | IP (IPv4/IPv6) | Server-client addressing and packet routing |
| Network Access Layer | Ethernet / Wi-Fi | Physical or wireless network transmission |

## 6.3 Serialization

The system must use JSON for client-server data exchange. JSON is required because:

1. It is simple and compact enough for network communication.
2. It can represent objects, arrays, and nested structures.
3. It is natively supported by web clients and common server frameworks.
4. It is easy to inspect during demonstration and debugging.

## 7. Protocol Requirements

## 7.1 HTTP Requests

HTTP should be used for request-response operations, including:

1. Login.
2. Logout.
3. Fetch online users.
4. Fetch room list.
5. Submit room creation request.
6. Approve room request.
7. Reject room request.
8. Create room directly.
9. Delete room.
10. Fetch chat history.
11. Fetch server logs.

## 7.2 WebSocket Events

WebSocket or equivalent socket-based real-time communication should be used for live events, including:

1. Room message delivery.
2. Private message delivery.
3. Announcement delivery.
4. User joined room notification.
5. User left room notification.
6. User kicked notification.
7. Room created notification.
8. Room deleted notification.
9. Online user status updates.

## 7.3 Standard Request Envelope

```json
{
  "type": "command_name",
  "request_id": "unique-request-id",
  "payload": {}
}
```

## 7.4 Standard Response Envelope

```json
{
  "type": "response_name",
  "request_id": "same-request-id",
  "success": true,
  "message": "Human readable message",
  "payload": {}
}
```

## 7.5 Standard Event Envelope

```json
{
  "type": "event_name",
  "payload": {}
}
```

## 7.6 Standard Error Envelope

```json
{
  "type": "error",
  "request_id": "req-001",
  "success": false,
  "message": "Permission denied",
  "payload": {
    "code": "PERMISSION_DENIED"
  }
}
```

## 8. Authentication and Authorization

## 8.1 Authentication

The server must:

1. Allow users to login with username and password.
2. Reject invalid credentials.
3. Assign a role after successful login.
4. Store authenticated session data server-side.
5. Reject or safely handle duplicate active login when needed.
6. Block protected features before login.
7. Use the authenticated session identity instead of trusting usernames from client payloads.

## 8.2 Authorization

The server must enforce permissions for every protected action:

1. Only Admin can approve or reject room requests.
2. Only Admin can create rooms directly.
3. Only Admin can delete rooms.
4. Only Admin can view server logs.
5. Pengajar can request class rooms.
6. Pelajar can request group discussion rooms.
7. Pengajar can send announcements to rooms they manage.
8. Pengajar can kick Pelajar from rooms they manage.
9. Admin can kick users from any room.
10. Users can send room messages only to rooms they have joined.
11. Users can view room history only for rooms they are allowed to access.

## 9. Seed Users

The application should include these demo users:

```text
admin / admin123 / admin
pengajar1 / pengajar123 / pengajar
pengajar2 / pengajar123 / pengajar
pelajar1 / pelajar123 / pelajar
pelajar2 / pelajar123 / pelajar
pelajar3 / pelajar123 / pelajar
```

## 10. Functional Requirements

## 10.1 Web Client

The web client must:

1. Provide a login screen.
2. Show role-appropriate navigation after login.
3. Show online users.
4. Show room list.
5. Show pending room requests to Admin.
6. Provide room request forms for Pengajar and Pelajar.
7. Provide room approval and rejection controls for Admin.
8. Provide room creation and deletion controls for Admin.
9. Provide a chat interface for joined rooms.
10. Provide private message functionality.
11. Provide announcement functionality for Pengajar.
12. Display real-time incoming messages and system events.
13. Display chat history.
14. Display clear error messages.
15. Prevent users from seeing controls they cannot use.

## 10.2 Server Startup

The server must:

1. Start an HTTP server for browser clients.
2. Start a WebSocket or socket endpoint for real-time events.
3. Connect to the database.
4. Initialize required tables if they do not exist.
5. Seed demo users when appropriate.
6. Log startup information.
7. Handle server errors without exposing sensitive data to clients.

## 10.3 Login

The login flow must:

1. Accept username and password.
2. Validate credentials on the server.
3. Return the authenticated role.
4. Create a server-side session or token.
5. Mark the user online.
6. Notify relevant clients about online user updates.
7. Return a structured error for invalid credentials.

## 10.4 Logout and Disconnect

The server must:

1. Allow users to logout.
2. Mark users offline after logout or disconnect.
3. Clean up active WebSocket connections.
4. Remove disconnected users from active room connection state.
5. Keep persisted room membership and message history intact.
6. Broadcast online status updates when appropriate.

## 10.5 Online User List

Authenticated users can request online users. Each entry must include:

1. Username.
2. Role.
3. Online status.

## 10.6 Room Creation Request

Pengajar and Pelajar can submit room creation requests.

Room requests must include:

1. Requested room name.
2. Optional room description.
3. Requester username.
4. Requester role.
5. Request reason or room purpose.
6. Request status: pending, approved, or rejected.
7. Created timestamp.
8. Reviewed timestamp when approved or rejected.
9. Reviewer username when approved or rejected.

## 10.7 Room Request Approval

Admin can approve pending room requests.

Approval must:

1. Validate that the request exists.
2. Validate that the request is still pending.
3. Create the requested room.
4. Store creator and source request information.
5. Mark the request as approved.
6. Notify the requester when online.
7. Log the approval.

## 10.8 Room Request Rejection

Admin can reject pending room requests.

Rejection must:

1. Validate that the request exists.
2. Validate that the request is still pending.
3. Store an optional rejection reason.
4. Mark the request as rejected.
5. Notify the requester when online.
6. Log the rejection.

## 10.9 Direct Room Creation

Admin can create rooms directly without a request.

Direct room creation must:

1. Validate room name.
2. Prevent duplicate active room names.
3. Store creator information.
4. Make the room visible in the room list.
5. Broadcast a room created event.
6. Log room creation.

## 10.10 Room Deletion

Admin can delete rooms.

Room deletion must:

1. Validate that the room exists.
2. Mark the room inactive or remove it according to implementation policy.
3. Remove active users from the room connection state.
4. Notify affected users.
5. Preserve history when possible for audit and demonstration.
6. Log room deletion.

## 10.11 Room List

Authenticated users can request active rooms. Each room entry must include:

1. Room name.
2. Description when available.
3. Creator.
4. Member count.
5. Room status.

## 10.12 Join Room

Authenticated users can join existing active rooms.

The server must:

1. Check that the room exists.
2. Check that the room is active.
3. Prevent duplicate join.
4. Add the user to room membership.
5. Send confirmation to the user.
6. Broadcast a system message to room members.
7. Log the join event.

## 10.13 Leave Room

Authenticated users can leave rooms they have joined.

The server must:

1. Reject leaving rooms the user has not joined.
2. Remove the user from active room membership.
3. Send confirmation to the user.
4. Broadcast a system message to remaining room members.
5. Log the leave event.

## 10.14 Room Messages

Users can send messages to rooms they have joined.

The server must:

1. Validate room membership.
2. Reject empty messages.
3. Generate a server timestamp.
4. Save the message to history.
5. Broadcast the message only to active room members.
6. Log message metadata without exposing sensitive content unnecessarily.

## 10.15 Announcements

Pengajar can send announcements to rooms they manage. Admin can send announcements to any room.

Announcements must:

1. Validate sender permission.
2. Validate target room.
3. Reject empty announcement content.
4. Generate a server timestamp.
5. Save the announcement to message history.
6. Broadcast the announcement to room members with a distinct event type.
7. Log announcement metadata.

## 10.16 Private Messages

Users can send private messages to online users.

The server must:

1. Check that the target user exists.
2. Check that the target user is online.
3. Reject empty messages.
4. Generate a server timestamp.
5. Save the private message to history.
6. Send the private message only to the target user.
7. Send delivery confirmation to the sender.
8. Log private message metadata without logging message content.

## 10.17 Kick User

Admin can kick users from any room. Pengajar can kick Pelajar from rooms managed by that Pengajar.

Kick behavior must:

1. Validate kicker permission.
2. Validate target user.
3. Validate target room.
4. Reject kicking users who are not in the room.
5. Remove the target user from the room.
6. Notify the kicked user.
7. Notify remaining room members.
8. Log the kick event.

## 10.18 Chat History

Users can request recent room chat history.

The server must:

1. Check that the user can access the room.
2. Return recent room messages and announcements.
3. Include sender, content, message type, and timestamp.
4. Support a configurable limit.

Default history limit: 20 messages.

## 10.19 Server Logs

Admin can view server activity logs.

The server must log:

1. Server started.
2. User connected.
3. User disconnected.
4. Login success.
5. Login failed.
6. Room request submitted.
7. Room request approved.
8. Room request rejected.
9. Room created.
10. Room deleted.
11. User joined room.
12. User left room.
13. Room message sent.
14. Announcement sent.
15. Private message sent.
16. User kicked.
17. Invalid command or request.
18. Invalid JSON.
19. Permission denied.
20. Internal error.

Logs must not include passwords or private message contents.

## 11. Data Requirements

## 11.1 users

```text
id
username
password_hash
role
created_at
```

Password hashing is recommended. Plain passwords are acceptable only for a short local demonstration if explicitly documented.

## 11.2 rooms

```text
id
room_name
description
created_by
source_request_id
managed_by
is_active
created_at
deleted_at
```

## 11.3 room_requests

```text
id
room_name
description
requested_by
requester_role
purpose
status
reviewed_by
rejection_reason
created_at
reviewed_at
```

## 11.4 room_members

```text
id
room_id
username
joined_at
left_at
is_active
```

## 11.5 messages

```text
id
message_id
room_name
sender
receiver
message_type
content
timestamp
deleted
deleted_by
deleted_at
```

Message types:

```text
room_message
private_message
system_message
announcement
room_created
room_deleted
room_request_submitted
room_request_approved
room_request_rejected
user_kicked
```

Phase 1 persistence stores Message Center messages in SQLite, including room messages, private messages, announcements, system/feed events, timestamps, stable message IDs, and admin deletion metadata.

## 11.6 server_logs

```text
id
event_type
username
description
timestamp
```

## 12. Error Handling Requirements

The server must return structured errors and must not crash on bad input.

Handle:

1. Invalid JSON.
2. Unknown request type.
3. Missing payload.
4. Missing required field.
5. Not authenticated.
6. Invalid username or password.
7. Duplicate active login.
8. Permission denied.
9. Room request not found.
10. Room request already reviewed.
11. Room already exists.
12. Room not found.
13. Room inactive.
14. User already in room.
15. User not in room.
16. Empty message.
17. Target user not found.
18. Target user offline.
19. Invalid kick target.
20. WebSocket disconnect.
21. Database error.
22. Internal server error.

## 13. Security Requirements

1. Do not print passwords in logs.
2. Do not print private message contents in logs.
3. Do not trust role or username from client payload after login.
4. Use authenticated server-side session identity.
5. Check role permissions on the server.
6. Reject protected features before login.
7. Handle malformed payloads safely.
8. Keep private messages visible only to sender and receiver.
9. Protect Admin-only endpoints from non-Admin users.
10. Use password hashing if time allows.
11. Avoid exposing stack traces to the web client.

## 14. Recommended Folder Structure

```text
mbg/
|
|-- server/
|   |-- main.py
|   |-- app.py
|   |-- auth_service.py
|   |-- room_service.py
|   |-- request_service.py
|   |-- message_service.py
|   |-- realtime_service.py
|   |-- logger_service.py
|   |-- database.py
|   |-- protocol.py
|   `-- models.py
|
|-- web/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|   `-- assets/
|
|-- data/
|   `-- mbg.db
|
|-- docs/
|   |-- protocol.md
|   |-- commands.md
|   `-- demo-script.md
|
|-- tests/
|   |-- test_auth.py
|   |-- test_room_service.py
|   |-- test_request_service.py
|   |-- test_message_service.py
|   `-- test_protocol.py
|
|-- README.md
`-- requirements.txt
```

If the repository already has an established structure, adapt to it instead of rewriting everything unnecessarily.

## 15. Module Responsibilities

## 15.1 server/main.py

Responsible for:

1. Parsing server configuration.
2. Starting the HTTP server.
3. Starting the WebSocket or realtime endpoint.
4. Printing startup information.

## 15.2 server/app.py

Responsible for:

1. Defining HTTP routes.
2. Connecting routes to services.
3. Returning JSON responses.
4. Handling request validation errors.

## 15.3 server/auth_service.py

Responsible for:

1. Seed users.
2. Login validation.
3. Role lookup.
4. Session checks.
5. Permission checks.

## 15.4 server/room_service.py

Responsible for:

1. Creating rooms.
2. Deleting rooms.
3. Listing rooms.
4. Joining rooms.
5. Leaving rooms.
6. Checking room membership.
7. Returning member counts.
8. Enforcing managed room behavior.

## 15.5 server/request_service.py

Responsible for:

1. Creating room requests.
2. Listing pending requests.
3. Approving requests.
4. Rejecting requests.
5. Storing review metadata.

## 15.6 server/message_service.py

Responsible for:

1. Room message handling.
2. Private message handling.
3. Announcement handling.
4. Timestamp creation.
5. Message persistence.
6. Chat history retrieval.

## 15.7 server/realtime_service.py

Responsible for:

1. Managing active WebSocket connections.
2. Routing room events.
3. Routing private events.
4. Broadcasting system notifications.
5. Cleaning up disconnected clients.

## 15.8 server/logger_service.py

Responsible for:

1. Terminal logs.
2. Optional file logs.
3. Database logs.
4. Sensitive-data filtering.

## 15.9 server/database.py

Responsible for:

1. Database connection.
2. Table creation.
3. Seed data.
4. Query helpers.
5. Transaction handling.

## 15.10 web/index.html

Responsible for:

1. Application shell.
2. Login view.
3. Role-specific panels.
4. Chat view containers.

## 15.11 web/styles.css

Responsible for:

1. Layout.
2. Responsive styling.
3. Role and message visual states.

## 15.12 web/app.js

Responsible for:

1. Browser-side event handling.
2. HTTP request calls.
3. WebSocket connection.
4. Rendering room lists, messages, requests, and logs.
5. Showing user-facing errors.

## 16. Implementation Plan

## Phase 1 - Web Client-Server Foundation

Goal: prove the browser client can communicate with the server.

Tasks:

1. Start HTTP server.
2. Serve or connect web client.
3. Return JSON health response.
4. Add WebSocket or realtime endpoint.
5. Prove browser can connect to realtime endpoint.
6. Document how to run the server and browser client.

## Phase 2 - Authentication and RBAC

Goal: identify users and enforce role privileges.

Tasks:

1. Add seed users.
2. Implement login.
3. Store session or token state.
4. Track online users.
5. Enforce Admin, Pengajar, and Pelajar permissions.
6. Hide unauthorized controls in the client.
7. Reject unauthorized actions on the server.

## Phase 3 - Room Request Workflow

Goal: match the SKPL room governance flow.

Tasks:

1. Pengajar can request class room creation.
2. Pelajar can request group discussion room creation.
3. Admin can view pending requests.
4. Admin can approve requests.
5. Admin can reject requests.
6. Approved requests create rooms.
7. Rejected requests store rejection metadata.

## Phase 4 - Room Management

Goal: manage active discussion rooms.

Tasks:

1. Admin can create rooms directly.
2. Admin can delete rooms.
3. Users can view room list.
4. Users can join rooms.
5. Users can leave rooms.
6. Member counts update correctly.
7. Room events are broadcast in real time.

## Phase 5 - Messaging

Goal: support real-time communication.

Tasks:

1. Send room messages.
2. Broadcast only to room members.
3. Send private messages.
4. Send Pengajar announcements.
5. Generate server timestamps.
6. Store message history.
7. Return chat history.

## Phase 6 - Moderation and Logs

Goal: support classroom control and auditability.

Tasks:

1. Admin can kick users from rooms.
2. Pengajar can kick Pelajar from managed rooms.
3. Server logs important events.
4. Admin can view logs.
5. Logs exclude passwords and private message content.

## Phase 7 - Database Persistence

Goal: preserve system data.

Tasks:

1. Create database tables.
2. Seed demo users.
3. Persist rooms.
4. Persist room requests.
5. Persist room membership.
6. Persist room messages.
7. Persist private messages.
8. Persist announcements.
9. Persist server logs.

## Phase 8 - Documentation and Demo

Goal: prepare final project submission.

Tasks:

1. Update README.
2. Document architecture and protocols.
3. Document role privileges.
4. Document demo accounts.
5. Write demo script.
6. Add troubleshooting notes.
7. Run manual tests.

## 17. Web Client Requirements

The browser client must include:

1. Login page.
2. Dashboard after login.
3. Online users panel.
4. Room list panel.
5. Pending room request panel for Admin.
6. Room request form for Pengajar and Pelajar.
7. Room creation form for Admin.
8. Chat panel for selected room.
9. Private message interface.
10. Announcement interface for Pengajar.
11. Server log view for Admin.
12. Clear loading, success, and error states.

## 18. Demo Script

## Step 1 - Start Server

```bash
python server/main.py
```

Expected:

```text
Server started
HTTP endpoint ready
Realtime endpoint ready
```

## Step 2 - Open Web Client

Open the web client in a browser.

Expected:

```text
Login screen is visible
```

## Step 3 - Login as Admin

```text
username: admin
password: admin123
```

Expected:

```text
Admin dashboard is visible
Pending room requests, room management, online users, and logs are accessible
```

## Step 4 - Login as Pengajar

```text
username: pengajar1
password: pengajar123
```

Expected:

```text
Pengajar dashboard is visible
Pengajar can request a class room
```

## Step 5 - Login as Pelajar

```text
username: pelajar1
password: pelajar123
```

Expected:

```text
Pelajar dashboard is visible
Pelajar can request a group discussion room
```

## Step 6 - Submit Room Request

Pengajar submits:

```text
room_name: progjar
purpose: Diskusi Program Jaringan
```

Expected:

```text
Request status is pending
Admin can see the request
```

## Step 7 - Approve Room Request

Admin approves the pending request.

Expected:

```text
Room progjar is created
Room list updates for users
Requester receives notification when online
```

## Step 8 - Join Room

Pengajar and Pelajar join `progjar`.

Expected:

```text
System messages show users joining
Member count updates
```

## Step 9 - Send Room Message

Pelajar sends:

```text
Halo semuanya
```

Expected:

```text
Message appears in real time for room members
```

## Step 10 - Send Announcement

Pengajar sends:

```text
Kelas dimulai pukul 10.00
```

Expected:

```text
Announcement appears distinctly for room members
```

## Step 11 - Send Private Message

Pengajar sends a private message to Pelajar.

Expected:

```text
Only the target Pelajar receives the private message
Sender receives delivery confirmation
```

## Step 12 - View History and Logs

User views room history. Admin views server logs.

Expected:

```text
History shows room messages and announcements
Logs show important metadata without passwords or private message contents
```

## 19. Manual Test Checklist

1. Server starts.
2. Browser client opens.
3. WebSocket or realtime connection succeeds.
4. Admin login succeeds.
5. Pengajar login succeeds.
6. Pelajar login succeeds.
7. Invalid login fails.
8. Online user list updates.
9. Pengajar can submit room request.
10. Pelajar can submit room request.
11. Admin can view pending room requests.
12. Admin can approve room request.
13. Admin can reject room request.
14. Approved request creates a room.
15. Rejected request does not create a room.
16. Admin can create room directly.
17. Admin can delete room.
18. Users can view room list.
19. Users can join room.
20. Duplicate join is rejected.
21. Users can leave room.
22. Room message works after joining.
23. Room message is rejected before joining.
24. Pengajar can send announcement.
25. Pelajar cannot send announcement.
26. Private message to online user works.
27. Private message to offline user returns error.
28. Admin can kick users.
29. Pengajar can kick Pelajar from managed room.
30. Unauthorized kick is rejected.
31. Chat history works.
32. Admin can view server logs.
33. Non-Admin users cannot view server logs.
34. Invalid JSON does not crash server.
35. Invalid request does not crash server.
36. User disconnect does not crash server.
37. Multiple users can chat at the same time.

## 20. Definition of Done

The project is complete when:

1. MBG runs as a client-server web application.
2. Browser clients can connect to the server.
3. HTTP request-response features work.
4. Real-time WebSocket or socket events work.
5. JSON serialization is used for data exchange.
6. Users can login.
7. Roles Admin, Pengajar, and Pelajar are enforced server-side.
8. Online user list works.
9. Pengajar can request class room creation.
10. Pelajar can request group discussion room creation.
11. Admin can approve room requests.
12. Admin can reject room requests.
13. Admin can create rooms directly.
14. Admin can delete rooms.
15. Users can view room list.
16. Users can join rooms.
17. Users can leave rooms.
18. Users can send room messages.
19. Pengajar can send announcements.
20. Users can send private messages.
21. Admin and authorized Pengajar moderation works.
22. Messages include server timestamps.
23. Chat history works.
24. Server logging works.
25. Data is persisted in a database.
26. Server handles disconnects.
27. Server handles invalid JSON.
28. Server handles invalid requests.
29. README explains how to run and demonstrate the project.
30. Demo script is ready and matches the SKPL.
