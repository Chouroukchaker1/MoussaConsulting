import React, { useEffect, useState, useMemo } from "react";
import { extract, fetchSecteurs } from "../api.js";

function todayISO(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

function downloadBlob(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function toCSV(rows) {
  if (!rows.length) return "";
  const headers = [
    "source_id",
    "title",
    "promoter_name",
    "publication_date",
    "expiration_date",
    "type",
    "nature",
    "url",
    "pdf_url",
  ];
  const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = [headers.join(",")];
  for (const r of rows) {
    lines.push(headers.map((h) => escape(r[h])).join(","));
  }
  return lines.join("\n");
}

export default function Dashboard({ username, onLogout }) {
  const [secteurs, setSecteurs] = useState([{ key: "tous", label: "Tous secteurs" }]);
  const [dateDebut, setDateDebut] = useState(todayISO(-7));
  const [dateFin, setDateFin] = useState(todayISO(0));
  const [secteur, setSecteur] = useState("tous");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const STORAGE_KEY = "boamp_last_result";

  // Load persisted result on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setResult(parsed);
      }
    } catch (e) {
      // ignore parse errors
    }
  }, []);

  useEffect(() => {
    fetchSecteurs()
      .then(setSecteurs)
      .catch(() => {
        /* la liste par défaut reste utilisable si l'appel échoue */
      });
  }, []);

  const secteurLabel = useMemo(
    () => secteurs.find((s) => s.key === secteur)?.label || secteur,
    [secteurs, secteur]
  );

  async function handleExtract(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const data = await extract(dateDebut, dateFin, secteur);
      setResult(data);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      } catch (err) {
        // ignore storage errors
      }
    } catch (err) {
      setError(err.message || "Échec de l'extraction");
    } finally {
      setLoading(false);
    }
  }

  function handleClearAll() {
    setResult(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      // ignore
    }
  }

  function handleExportJSON() {
    if (!result) return;
    downloadBlob(
      `boamp_${result.date_debut}_${result.date_fin}.json`,
      JSON.stringify(result.results, null, 2),
      "application/json"
    );
  }

  function handleExportCSV() {
    if (!result) return;
    downloadBlob(
      `boamp_${result.date_debut}_${result.date_fin}.csv`,
      toCSV(result.results),
      "text/csv"
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MoussaConsulting</span>
          <span className="brand-sub">Extraction BOAMP</span>
        </div>
        <div className="topbar-right">
          <span className="user-chip">{username}</span>
          <button className="btn-ghost" onClick={onLogout}>
            Déconnexion
          </button>
        </div>
      </header>

      <main className="main">
        <section className="panel">
          <h2 className="panel-title">Paramètres d'extraction</h2>
          <form onSubmit={handleExtract}>
            <div className="filter-grid">
              <div className="field">
                <label htmlFor="date_debut">Du</label>
                <input
                  id="date_debut"
                  type="date"
                  value={dateDebut}
                  onChange={(e) => setDateDebut(e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="date_fin">Au</label>
                <input
                  id="date_fin"
                  type="date"
                  value={dateFin}
                  onChange={(e) => setDateFin(e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="secteur">Secteur</label>
                <select
                  id="secteur"
                  value={secteur}
                  onChange={(e) => setSecteur(e.target.value)}
                >
                  {secteurs.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
              <button className="btn-extract" type="submit" disabled={loading}>
                {loading ? "Extraction en cours…" : "Lancer l'extraction"}
              </button>
            </div>
          </form>
          {error && <div className="error-banner" style={{ marginTop: 18 }}>{error}</div>}
        </section>

        <section className="panel">
          <div className="results-header">
            <div className="results-count">
              {result ? (
                <>
                  <b>{result.total}</b> annonce{result.total > 1 ? "s" : ""} · {secteurLabel} ·{" "}
                  {result.date_debut} → {result.date_fin}
                </>
              ) : (
                "Aucune extraction lancée"
              )}
            </div>
            {result && result.total > 0 && (
              <div className="export-actions">
                <button className="btn-small" onClick={handleExportCSV}>
                  Exporter CSV
                </button>
                <button className="btn-small" onClick={handleExportJSON}>
                  Exporter JSON
                </button>
                <button className="btn-small btn-danger" onClick={handleClearAll}>
                  Supprimer tout
                </button>
              </div>
            )}
          </div>

          {result && result.total > 0 ? (
            <table className="results-table">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Objet</th>
                  <th>Acheteur</th>
                  <th>Publication</th>
                  <th>Date limite</th>
                  <th>Statut</th>
                  <th>Liens</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((offre) => (
                  <tr key={offre.source_id}>
                    <td className="offre-ref">{offre.source_id}</td>
                    <td className="offre-title">{offre.title}</td>
                    <td>{offre.promoter_name}</td>
                    <td className="offre-ref">
                      {offre.publication_date ? offre.publication_date.slice(0, 10) : "—"}
                    </td>
                    <td className="offre-ref">
                      {offre.expiration_date ? offre.expiration_date.slice(0, 10) : "—"}
                    </td>
                    <td>
                      <span className={`badge ${offre.avis_id === 1 ? "badge-ao" : "badge-attrib"}`}>
                        {offre.avis_id === 1 ? "Appel d'offres" : "Attribution"}
                      </span>
                    </td>
                    <td>
                      <a className="offre-link" href={offre.url} target="_blank" rel="noreferrer">
                        BOAMP
                      </a>
                      {offre.pdf_url && (
                        <>
                          {" · "}
                          <a className="offre-link" href={offre.pdf_url} target="_blank" rel="noreferrer">
                            PDF
                          </a>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            result && (
              <div className="empty-state">
                <p className="empty-state-title">Aucune annonce trouvée</p>
                <p>Essayez une période plus large ou un autre secteur.</p>
              </div>
            )
          )}
        </section>
      </main>
    </div>
  );
}
