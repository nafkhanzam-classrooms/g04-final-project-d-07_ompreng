import { useEffect, useState } from "react";
import { Button } from "./common.jsx";
import { ROLE_LABELS } from "../utils/uiConstants.js";
import { EyeIcon, EyeOffIcon } from "./icons/UiIcons.jsx";

export function AccessPanel({ chat, variant = "auth" }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const isLoggedIn = Boolean(chat.session);
  const isRegister = chat.authMode === "register";

  useEffect(() => {
    if (!isLoggedIn) setPassword("");
  }, [isLoggedIn]);

  function submit(event) {
    event.preventDefault();
    if (isLoggedIn) return;
    chat.submitAuth({ username, password, role });
  }

  if (variant === "akun") {
    return (
      <section className="panel auth-panel" aria-labelledby="akunTitle">
        <div className="panel-heading">
          <h2 id="akunTitle">Account</h2>
        </div>
        {isLoggedIn ? (
          <div className="grid gap-[13px] p-4">
            <p className="inline-flex items-center gap-2 max-w-full min-h-[30px] px-[11px] border border-[rgba(15,23,42,0.12)] rounded-full bg-white text-[var(--ink)] overflow-hidden text-[0.78rem] font-black text-ellipsis whitespace-nowrap">
              {ROLE_LABELS[chat.session.role] || chat.session.role}: {chat.session.username}
            </p>
            <div className="grid grid-cols-1 gap-2.5">
              <Button variant="danger-outline" onClick={() => chat.send("logout")}>Sign Out</Button>
            </div>
          </div>
        ) : (
          <AuthForm
            username={username}
            password={password}
            role={role}
            isRegister={isRegister}
            isLoggedIn={isLoggedIn}
            notice={chat.authNotice}
            setUsername={setUsername}
            setPassword={setPassword}
            setRole={setRole}
            setAuthMode={chat.setAuthMode}
            onSubmit={submit}
          />
        )}
      </section>
    );
  }

  return (
    <section
      className="auth-card w-[min(520px,100%)] overflow-hidden rounded-[24px] border border-[rgba(15,23,42,0.06)] bg-white shadow-[0_30px_70px_rgba(30,58,138,0.16)]"
      aria-labelledby="authTitle"
    >
      <div className="flex flex-col items-center justify-start gap-2 px-10 pt-10 pb-0 text-center">
        <h2 className="text-[2rem] font-black tracking-[-0.015em]" id="authTitle">
          {isRegister ? "Create your account" : "Welcome to MBG"}
        </h2>
        <p className="m-0 text-[1.02rem] text-[var(--muted)]">
          {isRegister
            ? "Join your class as a student or teacher."
            : "Sign in as a student or teacher."}
        </p>
      </div>

      <AuthForm
        username={username}
        password={password}
        role={role}
        isRegister={isRegister}
        isLoggedIn={isLoggedIn}
        notice={chat.authNotice}
        setUsername={setUsername}
        setPassword={setPassword}
        setRole={setRole}
        setAuthMode={chat.setAuthMode}
        onSubmit={submit}
      />

      <p className="m-0 px-10 pt-[22px] pb-9 text-[var(--text-muted)] text-[0.96rem] text-center">
        {isRegister ? (
          <>
            Already have an account?{" "}
            <button
              type="button"
              className="border-0 bg-transparent p-0 text-primary font-extrabold cursor-pointer hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 rounded-[4px]"
              onClick={() => chat.setAuthMode("login")}
            >
              Sign in
            </button>
          </>
        ) : (
          <>
            New here?{" "}
            <button
              type="button"
              className="border-0 bg-transparent p-0 text-primary font-extrabold cursor-pointer hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2 rounded-[4px]"
              onClick={() => chat.setAuthMode("register")}
            >
              Create an account
            </button>
          </>
        )}
      </p>
    </section>
  );
}

function AuthForm({
  username,
  password,
  role,
  isRegister,
  isLoggedIn,
  notice,
  setUsername,
  setPassword,
  setRole,
  setAuthMode,
  onSubmit,
}) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <>
      <div
        className="segmented"
        role="tablist"
        aria-label="Authentication mode"
      >
        <button
          className={`segment auth-mode-segment ${!isRegister ? "active" : ""}`}
          type="button"
          disabled={isLoggedIn}
          onClick={() => setAuthMode("login")}
        >
          Sign In
        </button>
        <button
          className={`segment auth-mode-segment ${isRegister ? "active" : ""}`}
          type="button"
          disabled={isLoggedIn}
          onClick={() => setAuthMode("register")}
        >
          Register
        </button>
      </div>

      {notice && (
        <div
          className="mx-10 mt-5 rounded-[var(--radius-md)] border border-danger/20 bg-danger-bg px-4 py-3 text-[0.92rem] font-extrabold text-danger"
          role="alert"
        >
          {notice}
        </div>
      )}

      <form className="grid gap-5 px-10 pt-7 pb-2" onSubmit={onSubmit}>
        <label>
          <span className="text-[0.9rem] text-text font-extrabold">Username</span>
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter your username"
            autoComplete="username"
            required
            disabled={isLoggedIn}
            className="min-h-[50px] px-4 text-[1rem]"
          />
        </label>
        <label>
          <span className="text-[0.9rem] text-text font-extrabold">Password</span>
          <div className="relative block">
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
              disabled={isLoggedIn}
              className="min-h-[50px] px-4 pr-[52px] text-[1rem]"
            />
            <button
              type="button"
              className="absolute top-1/2 right-2 -translate-y-1/2 inline-flex items-center justify-center w-9 h-9 border-0 rounded-[var(--radius-sm)] bg-transparent text-[var(--text-muted)] cursor-pointer hover:text-text hover:bg-bg-soft focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              disabled={isLoggedIn}
            >
              {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          </div>
        </label>

        {isRegister && (
          <label>
            <span className="text-[0.9rem] text-text font-extrabold">Role</span>
            <select
              value={role}
              onChange={(event) => setRole(event.target.value)}
              disabled={isLoggedIn}
              className="min-h-[50px] px-4 text-[1rem]"
            >
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
            </select>
          </label>
        )}

        <div className="mt-1.5 grid grid-cols-1 gap-2.5">
          <Button
            variant="primary"
            className="min-h-[52px] text-[1.02rem]"
            type="submit"
            disabled={isLoggedIn}
          >
            {isRegister ? "Register" : "Sign In"}
          </Button>
        </div>
      </form>
    </>
  );
}
