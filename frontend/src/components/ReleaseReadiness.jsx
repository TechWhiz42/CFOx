import React, { useCallback, useEffect, useState } from "react";
import "./ReleaseReadiness.css";

export default function ReleaseReadiness({ authFetch }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await authFetch("/transactions/analytics/release-readiness");
      if (!response.ok) throw new Error(`Release readiness request failed (${response.status})`);
      setData(await response.json());
    } catch (err) {
      setError(err?.message || "Unable to load release readiness.");
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <section className="release-readiness"><div className="release-muted">Checking release readiness…</div></section>;
  if (error) return <section className="release-readiness"><div className="release-error">{error}</div></section>;
  if (!data) return null;

  return (
    <section className="release-readiness">
      <div className="release-header">
        <div>
          <div className="release-eyebrow">FINAL GATE</div>
          <h2>Release Readiness</h2>
          <p>Configuration checks for deployment confidence.</p>
        </div>
        <button onClick={load} disabled={loading}>{loading ? "Checking…" : "Refresh"}</button>
      </div>
      <div className={`release-status ${data.ready ? "ready" : "blocked"}`}>
        <strong>{data.ready ? "READY FOR DEPLOYMENT" : "DEPLOYMENT BLOCKED"}</strong>
        <span>{data.passed}/{data.total} checks passed</span>
      </div>
      <div className="release-checks">
        {data.checks.map((check) => (
          <div className="release-check" key={check.name}>
            <span className={`release-dot ${check.passed ? "ok" : "bad"}`} />
            <div><strong>{check.name}</strong><small>{check.detail}</small></div>
          </div>
        ))}
      </div>
    </section>
  );
}
