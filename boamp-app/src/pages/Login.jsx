import React, { useState } from "react";
import { login, setSession } from "../api.js";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      setSession(data.token, data.username);
      onLogin(data.username);
    } catch (err) {
      setError(err.message || "Connexion impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <p className="login-eyebrow">MoussaConsulting · Accès réservé</p>
        <h1 className="login-title">Extraction BOAMP</h1>
        <p className="login-sub">
          Connectez-vous pour extraire les annonces du Bulletin officiel des
          annonces de marchés publics.
        </p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="username">Identifiant</label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>

        <div className="login-footer">
          <span className="stamp">
            Accès
            <br />
            Sécurisé
          </span>
        </div>
      </div>
    </div>
  );
}
