[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/4SHtB1vz)

# Network Programming - Final Project [G04]

## Group Members

| Name | Student ID | Class |
| --- | --- | --- |
| Steven Alvin Christian | 5025241116 | D |
| Andie Azril Alfrianto | 5025241054 | D |
| Joaquin Fairuz Nawfal Ismono | 5025241106 | D |

## YouTube Link (Unlisted)

Click this video down below :D

[![Watch the video](https://i.ytimg.com/vi/Le1__bKaH4A/maxres3.jpg)](https://youtu.be/Le1__bKaH4A)

[https://youtu.be/Le1__bKaH4A](https://youtu.be/Le1__bKaH4A)

## Program Explanation

### Description

**MBG (Mari Belajar Guys)** is a **web-based multi-chat room application** designed to support learning communication and collaboration across multiple discussion rooms at the same time. Through this application, users can join different chat rooms based on topics or classes, send real-time messages, use private messaging, upload files, react to messages, and receive notifications about recent activities.

The main focus of this project is to build a multi-room communication system that allows many users to interact in several chat rooms simultaneously. Each room has its own conversation flow, so discussions between groups, courses, or learning topics can be more organized. In addition, the application also provides room request features and admin moderation to keep discussion room management controlled.

From the **Network Programming** perspective, MBG implements a client-server architecture with socket-based communication. The browser connects to a **WebSocket bridge**, then the bridge forwards messages to a **raw TCP server** using a newline-delimited JSON protocol. With this architecture, the application remains convenient to use through the web, while the core real-time communication between users and chat rooms still applies networking concepts, TCP sockets, and direct message exchange.

### Main Features

1. **Authentication**

   * Login using demo accounts.
   * Register for `student` and `teacher` roles.
   * Session resume using a token stored in browser session storage.
   * Passwords are stored using PBKDF2-SHA256 hashing.

2. **Role-Based Access Control**

   * `admin`: creates rooms, deletes rooms, approves/rejects room requests, views server activity, sends global announcements, moderates users and messages.
   * `teacher`: requests rooms, joins/leaves rooms, chats, sends private messages, sends announcements in joined rooms, kicks students from certain rooms.
   * `student`: requests rooms, joins/leaves rooms, chats, sends private messages, and reacts to messages.

### RBAC Table

| Capability                       | Admin | Teacher                                       | Student |
| -------------------------------- | ----- | --------------------------------------------- | ------- |
| Login                            | Yes   | Yes                                           | Yes     |
| Register from UI                 | No    | Yes                                           | Yes     |
| Resume session                   | Yes   | Yes                                           | Yes     |
| View online users                | Yes   | Yes                                           | Yes     |
| View room list                   | Yes   | Yes                                           | Yes     |
| Create room directly             | Yes   | No                                            | No      |
| Request new room                 | No    | Yes                                           | Yes     |
| Approve room request             | Yes   | No                                            | No      |
| Reject room request              | Yes   | No                                            | No      |
| Join room                        | Yes   | Yes                                           | Yes     |
| Leave room                       | Yes   | Yes                                           | Yes     |
| Delete room                      | Yes   | No                                            | No      |
| Send room message                | Yes   | Yes                                           | Yes     |
| Send private message             | Yes   | Yes                                           | Yes     |
| Send room announcement           | Yes   | Yes, if room member                           | No      |
| Send global announcement         | Yes   | No                                            | No      |
| Upload/send attachment           | Yes   | Yes                                           | Yes     |
| React to room/private messages   | Yes   | Yes                                           | Yes     |
| Delete messages                  | Yes   | No                                            | No      |
| Kick users from room             | Yes   | Student only, if the teacher is a room member | No      |
| View pending room requests       | Yes   | No                                            | No      |
| View system activity/server logs | Yes   | No                                            | No      |

3. **Room Management**

   * Admins can create and delete rooms.
   * Teachers/students can submit room requests.
   * Admins can approve or reject room requests with a reason.
   * The system prevents duplicate pending requests for the same room.

4. **Messaging**

   * Room chat.
   * Private messages between users.
   * Room announcements.
   * Global announcements for all users.
   * Message history for rooms, private chats, and notification feeds.
   * Multiline message support.

5. **Attachment**

   * Users can upload files.
   * Files are sent as message attachments.
   * Files use download tokens so access can be more controlled.

6. **Reaction and Moderation**

   * Reactions: `agree`, `disagree`, `like`, `funny`, and `confused`.
   * Admins can soft-delete messages.
   * Reactions are not available for notification/feed messages.

7. **Realtime Update**

   * Online user list.
   * Room list updates.
   * Incoming room/private messages.
   * Pending request updates.
   * Server activity updates for admins.

8. **Toast Feedback**

   * Action responses are displayed as toast notifications at the top center of the screen.
   * Toasts have success/error/info icons, short descriptions, a close button, and an auto-dismiss progress bar.

9. **Performance Monitoring and Load Test**

   * The TCP server displays periodic performance logs.
   * A Locust file is available to test the raw TCP server.
   * Visible metrics include request count, failure count, latency, RPS, and summary.

### Tech Stack

| Layer                      | Technology                                       |
| -------------------------- | ------------------------------------------------ |
| Frontend                   | React 19, Vite 8, Tailwind CSS 4                 |
| Backend                    | Python 3.10+, standard library socket, threading |
| Web Bridge                 | Python socketserver, manual WebSocket handling   |
| Protocol                   | JSON over TCP, newline-delimited framing         |
| Realtime Browser Transport | WebSocket `/ws`                                  |
| Database                   | SQLite                                           |
| Authentication Security    | PBKDF2-SHA256 password hashing                   |
| File Storage               | Local filesystem under `data/uploads/`           |
| Testing                    | Python `unittest`                                |
| Load Testing               | Locust TCP user                                  |

### Setup & Installation Guide

#### 1. Clone the repository

```bash
git clone https://github.com/nafkhanzam-classrooms/g04-final-project-d-07_ompreng.git
cd MBG
```

#### 2. Install frontend dependencies

```bash
cd frontend
pnpm install
cd ..
```

#### 3. Install optional load test dependencies

```bash
python -m pip install locust psutil
```

#### 4. Run the application

The easiest way is to use the runner:

```bash
python run.py
```

The runner will:

1. Build the React frontend into `frontend/dist`.
2. Start the TCP server on port `5000`.
3. Start the web bridge on port `8000`.

Then open:

```text
https://127.0.0.1:8000
```

The browser may show a certificate warning because the application uses a self-signed certificate for local development. Choose continue/advanced to enter the application.

#### 5. Run services manually

Build the frontend:

```bash
cd frontend
pnpm run build
cd ..
```

Start the TCP server:

```bash
python backend/server/main.py --host 0.0.0.0 --port 5000
```

Start the web bridge:

```bash
python backend/server/web_bridge.py --host 127.0.0.1 --port 8000 --mbg-host 127.0.0.1 --mbg-port 5000
```

#### 6. Demo Accounts

| Username   | Password     | Role    |
| ---------- | ------------ | ------- |
| `admin`    | `admin123`   | admin   |
| `teacher1` | `teacher123` | teacher |
| `teacher2` | `teacher123` | teacher |
| `student1` | `student123` | student |
| `student2` | `student123` | student |

Default rooms provided:

| Room      | Description               |
| --------- | ------------------------- |
| `general` | General discussion        |
| `progjar` | Network Programming class |

### Application Flow

#### User Flow

1. The user opens `https://127.0.0.1:8000`.
2. The browser loads the static frontend from `frontend/dist`.
3. The frontend opens a WebSocket connection to the `/ws` endpoint.
4. The user logs in or registers.
5. The frontend sends a JSON request with `type`, `request_id`, and `payload`.
6. The web bridge forwards the request to the TCP server.
7. The TCP server processes the request through the command handler and service layer.
8. The server sends a response with the same `request_id`.
9. The frontend matches the response with the pending action.
10. The UI is updated through React state and realtime events.

#### Room Request Flow

1. A student/teacher fills in the room name, description, and purpose.
2. The frontend sends the `request_room` command.
3. The server stores the request with `pending` status.
4. Admin receives a pending request update.
5. Admin can approve or reject it.
6. If approved, the room is created and the room list is broadcast to all users.
7. If rejected, the request status changes and the user sees a notification.

#### Chat Flow

1. The user selects a room or private message thread.
2. The user types a message.
3. The frontend sends `send_room_message` or `send_private_message`.
4. The server validates the session, role, membership, target user, and message content.
5. The message is stored in SQLite.
6. The server broadcasts the event to the relevant participants.
7. The frontend receives the event and adds the message to the active thread.

### Software Architecture

The application architecture uses a layered pattern:

```text
Browser UI
  |
  | HTTPS static files + WebSocket /ws
  v
Web Bridge
  |
  | JSON line protocol over TCP/TLS
  v
TCP Server
  |
  | Command Router
  v
Service Layer
  |
  | SQLite + Local Filesystem
  v
Persistence Layer
```

#### 1. Frontend Layer

The frontend is located in `frontend/src`. The main parts are:

* `App.jsx`: main application layout, header, sidebar, class panel, and toast.
* `AccessPanel.jsx`: login and register.
* `MessageCenter.jsx`: room chat, private message, notifications, composer, attachment, reaction.
* `RoomPanel.jsx`: create room, request room, join/leave/delete room.
* `PendingRequestsPanel.jsx`: approve/reject room requests.
* `ManageUsersPanel.jsx`: user moderation.
* `SystemActivity.jsx`: activity log for admins.
* `useMbgChat.js`: central state management and application event handling.
* `mbgTransport.js`: WebSocket wrapper, request-response tracking, timeout, pending action, and reconnect.

#### 2. Web Bridge Layer

The web bridge is located in `backend/server/web_bridge.py` and `backend/server/transport/web/`.

Bridge responsibilities:

* Serve built frontend files from `frontend/dist`.
* Accept WebSocket connections at `/ws`.
* Forward browser messages to the TCP server.
* Convert TCP server responses/events into WebSocket messages.
* Handle attachment upload/download.
* Support TLS/self-signed certificates for local demo purposes.

#### 3. TCP Server Layer

The TCP server is located in `backend/server/transport/tcp/server.py`.

TCP server responsibilities:

* Open a socket server on port `5000`.
* Accept multiple clients using thread-per-client.
* Read newline-delimited JSON messages.
* Send responses according to `request_id`.
* Broadcast events to users, rooms, admins, or all clients.
* Record performance statistics.

#### 4. Command Router

The command router is located in `backend/server/transport/tcp/commands.py`.

The router maps commands such as:

* `login`
* `register`
* `resume_session`
* `room_list`
* `request_room`
* `approve_room_request`
* `reject_room_request`
* `join_room`
* `leave_room`
* `send_room_message`
* `send_private_message`
* `send_announcement`
* `send_global_announcement`
* `toggle_reaction`
* `chat_history`
* `server_logs`

#### 5. Service Layer

The service layer is located in `backend/server/services/`.

* `auth.py`: login, register, role lookup, password verification.
* `room.py`: room, membership, room request, approval, rejection, permission.
* `message.py`: room message, private message, feed event, reaction, attachment, history.

#### 6. Persistence Layer

The SQLite database is located at `data/mbg.db`.

Main tables:

* `users`
* `rooms`
* `room_members`
* `room_requests`
* `messages`
* `message_reactions`
* `message_attachments`
* `pending_attachments`
* `server_logs`

Runtime files created:

* `data/mbg.db`
* `data/server.crt`
* `data/server.key`
* `data/uploads/`
* `data/*.log`

### Protocols

#### Browser to Bridge

The browser uses WebSocket:

```text
wss://127.0.0.1:8000/ws
```

Messages are sent as JSON strings.

#### Bridge to TCP Server

The bridge forwards messages to the TCP server using newline-delimited JSON:

```text
<json_object>\n
```

Example request:

```json
{
  "type": "send_room_message",
  "request_id": "req-123",
  "payload": {
    "room_name": "general",
    "content": "Hello everyone"
  }
}
```

Example success response:

```json
{
  "type": "send_room_message_response",
  "request_id": "req-123",
  "success": true,
  "message": "Room message sent",
  "payload": {
    "room_name": "general"
  }
}
```

Example error response:

```json
{
  "type": "error",
  "request_id": "req-123",
  "success": false,
  "message": "Please login before using this command",
  "payload": {
    "code": "NOT_AUTHENTICATED"
  }
}
```

The server also sends push events without being requested by the client, for example:

* `room_message`
* `private_message`
* `room_list_updated`
* `pending_room_requests_updated`
* `server_logs_updated`
* `global_announcement`

### State Management

Application state management is handled in React without external libraries such as Redux. The central state is located in the custom hook `useMbgChat.js`.

Important state:

* `session`: data of the currently logged-in user.
* `connected`: WebSocket connection status.
* `onlineUsers`: list of online users.
* `rooms`: list of rooms and members.
* `pendingRequests`: list of room requests waiting for approval.
* `threads`: room chat, private message, and notification thread data.
* `activeThreadKey`: currently opened thread.
* `selectedRoom`: room currently selected in the class panel.
* `pendingActions`: actions waiting for a response.
* `actionNotice`: toast feedback for the user.

State flow:

1. The UI calls a function from `useMbgChat`, such as `send`, `openThread`, or `startDirectMessage`.
2. `MbgTransport` sends JSON through WebSocket.
3. If a command requires a response, the request is stored in `pendingResponses`.
4. When the response arrives, the `request_id` is matched.
5. The state is updated according to the event type.
6. React components automatically re-render.
7. The user receives feedback through toast notifications and UI changes.

The session is temporarily stored in `sessionStorage` so the browser can perform `resume_session` after refresh.

### Security and Validation

Several security and validation mechanisms are implemented:

* Passwords are stored as PBKDF2-SHA256 hashes, not plaintext.
* Role-based access control is enforced on the server, not only in the UI.
* Commands other than `ping`, `login`, `register`, and `resume_session` must have a session.
* The server validates payloads to prevent empty messages, invalid targets, missing rooms, permission denied actions, and duplicate pending room requests.
* Message attachments use upload tickets and download tokens.
* JSON lines have a maximum size limit so oversized requests can be rejected.

### Testing

Run unit tests:

```bash
python -m unittest discover -s tests
```

Build the frontend:

```bash
cd frontend
pnpm run build
```

TCP load test:

```powershell
$env:MBG_HOST="127.0.0.1"
$env:MBG_PORT="5000"
$env:MBG_USE_SSL="1"
locust -f tests/performance/locustfile.py
```

Locust tests commands such as:

* `register`
* `login`
* `join_room`
* `ping`
* `room_list`
* `online_users`
* `feed_history`
* `chat_history`
* `send_room_message`
* `logout`

If the TCP server is run with the `--no-ssl` flag, change the environment variable to:

```powershell
$env:MBG_USE_SSL="0"
```

### Conclusion

MBG demonstrates the implementation of a class chat application with fairly complete Network Programming concepts. This system not only sends messages between clients, but also includes authentication, role-based permission, room workflows, realtime events, a WebSocket bridge, a raw TCP protocol, SQLite persistence, file upload, moderation, monitoring, and load testing.

The WebSocket-to-TCP bridge design makes the application convenient to use through a browser, while the main server still preserves the networking characteristics of the assignment through TCP sockets and newline-delimited JSON framing. With the separation of frontend, bridge, TCP server, service layer, and database, the code becomes easier to test, develop, and explain during the demo.
