import React, {useEffect, useState} from "react";
import "./CFORecommendations.css";

export default function CFORecommendations({authFetch, onAskCFO}) {
    const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState("");

    async function load() {
        setLoading(true);
        setError("");
        try {
            const r = await authFetch("/transactions/analytics/cfo-recommendations");
            if (!r.ok) throw new Error("Unable to load CFO recommendations.");
            setData(await r.json());
        } catch (e) {
            setError(e.message || "Unable to load recommendations.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load()
    }, []);
    if (loading) return <section className="cfo-recommendations">Generating recommendations…</section>;
    if (error) return <section className="cfo-recommendations">{error}</section>;
    const recs = data?.recommendations || [];
    return <section className="cfo-recommendations">
        <div className="cfo-rec-header">
            <div><span>CFO INTELLIGENCE</span><h2>What should I do next?</h2>
                <p>Recommendations derived from financial signals and decision simulations.</p></div>
            <button onClick={load}>Refresh</button>
        </div>
        {!recs.length ? <div>No high-priority recommendations right now.</div> :
            <div className="cfo-rec-list">{recs.map((x, i) => <article className="cfo-rec-card" key={x.category + i}>
                <b>{x.priority}</b>
                <div className="cfo-rec-body"><strong>{x.title}</strong>
                    <div>{x.recommendation}</div>
                    <small>{x.basis}</small></div>
                <button onClick={() => onAskCFO?.(`Explain this recommendation: ${x.recommendation}`)}>Ask CFOx</button>
            </article>)}</div>}
    </section>;
}
