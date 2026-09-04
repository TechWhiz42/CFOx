import React, {useEffect, useState} from "react";
import "./ProactiveCFO.css";

export default function ProactiveCFO({authFetch, onInvestigate, onAskCFO}) {
    const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState("");

    async function load() {
        setLoading(true);
        try {
            const r = await authFetch("/transactions/analytics/proactive-cfo");
            if (!r.ok) throw Error("Unable to load proactive CFO alerts.");
            setData(await r.json())
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        load()
    }, []);
    if (loading) return <section className="proactive-cfo">Scanning financial signals…</section>;
    if (error) return <section className="proactive-cfo">{error}</section>;
    const a = data?.alerts || [];
    return <section className="proactive-cfo">
        <div className="proactive-header">
            <div><span>PROACTIVE CFO</span><h2>Early-Warning Center</h2><p>CFOx checks financial signals and configured
                targets for items that deserve review.</p></div>
            <button onClick={load}>Refresh</button>
        </div>
        {!a.length ? <div>No current high-priority signals.</div> :
            <div className="proactive-list">{a.map((x, i) => <article className="proactive-card" key={x.category + i}>
                <b>{x.severity.toUpperCase()}</b>
                <div className="proactive-body"><strong>{x.title}</strong>
                    <div>{x.message}</div>
                    <small>{x.source}</small><p>{x.recommended_action}</p></div>
                <div className="proactive-actions">
                    <button onClick={() => onInvestigate?.(x)}>Investigate</button>
                    <button onClick={() => onAskCFO?.(`Why is this alert important: ${x.message}`)}>Ask CFOx</button>
                </div>
            </article>)}</div>}</section>
}
