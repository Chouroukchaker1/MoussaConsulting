import React, { useState, useEffect } from "react";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import { getToken, getUsername, clearSession } from "./api.js";

export default function App() {
  const [session, setSessionState] = useState(null);

  useEffect(() => {
    const token = getToken();
    const username = getUsername();
    if (token && username) setSessionState({ token, username });
  }, []);

  function handleLogin(username) {
    setSessionState({ token: getToken(), username });
  }

  function handleLogout() {
    clearSession();
    setSessionState(null);
  }

  if (!session) {
    return <Login onLogin={handleLogin} />;
  }

  return <Dashboard username={session.username} onLogout={handleLogout} />;
}
