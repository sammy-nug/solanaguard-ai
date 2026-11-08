import { FormEvent, useState } from "react";
import { AnalysisResponse, analyzeTransaction } from "./services/api";

function App() {
  const [signature, setSignature] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    setIsLoading(true);
    try { setResult(await analyzeTransaction(signature.trim())); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to analyze this transaction."); }
    finally { setIsLoading(false); }
  }

  return (
    <main className="app-shell">
      <header className="masthead"><div><p className="eyebrow">SOLANAGUARD AI / DEVNET</p><h1>Understand before you sign.</h1><p className="lede">A deterministic transaction review with a plain-language AI explanation.</p></div><span className="status-dot">READ ONLY</span></header>
      <section className="input-panel"><form onSubmit={submit}><label htmlFor="signature">Transaction signature</label><div className="input-row"><input id="signature" value={signature} onChange={(event) => setSignature(event.target.value)} placeholder="Paste a confirmed Devnet signature" autoComplete="off" required /><button type="submit" disabled={isLoading || !signature.trim()}>{isLoading ? "Analyzing..." : "Analyze transaction"}</button></div></form>{error && <p className="error-message">{error}</p>}</section>
      {result && <AnalysisReport result={result} />}
    </main>
  );
}

function AnalysisReport({ result }: { result: AnalysisResponse }) {
  const { transaction, analysis, ai_explanation: ai } = result;
  const limitations = [...transaction.warnings, ...analysis.warnings, ...ai.limitations];
  return (
    <div className="report-grid">
      <section className={`score-panel score-${analysis.category}`}><p className="eyebrow">DETERMINISTIC ASSESSMENT</p><div className="score-number">{analysis.score}</div><p className="score-label">{analysis.category.replace("_", " ")}</p><p className="muted">Heuristic indicator, not a safety guarantee.</p></section>
      <section className="facts-panel"><p className="eyebrow">TRANSACTION FACTS</p><dl className="facts-list"><div><dt>Signature</dt><dd className="mono">{transaction.signature}</dd></div><div><dt>Network</dt><dd>{transaction.network}</dd></div><div><dt>Status</dt><dd>{transaction.status}</dd></div><div><dt>Slot</dt><dd>{transaction.slot ?? "Unavailable"}</dd></div><div><dt>Fee</dt><dd>{transaction.fee == null ? "Unavailable" : `${transaction.fee} lamports`}</dd></div></dl></section>
      <section className="findings-panel full-width"><div className="section-heading"><div><p className="eyebrow">SECURITY FINDINGS</p><h2>What the rules found</h2></div><span className="finding-count">{analysis.findings.length} findings</span></div>{analysis.findings.length === 0 ? <p className="muted">No deterministic indicators were found in the available data. This does not guarantee safety.</p> : <div className="finding-list">{analysis.findings.map((finding) => <article className="finding" key={finding.code}><div className="finding-topline"><strong>{finding.title}</strong><span>{finding.kind}</span></div><p>{finding.explanation}</p>{finding.evidence.map((evidence) => <p className="evidence" key={evidence}>{evidence}</p>)}</article>)}</div>}</section>
      <section className="ai-panel full-width"><div className="section-heading"><div><p className="eyebrow">BACKBOARD AI</p><h2>Plain-language explanation</h2></div><span className={ai.available ? "availability available" : "availability"}>{ai.available ? "AVAILABLE" : "UNAVAILABLE"}</span></div>{ai.available ? <div className="ai-content"><p className="ai-summary">{ai.summary}</p><div className="ai-columns"><div><h3>Risk context</h3><p>{ai.risk_explanation}</p></div><div><h3>What to verify</h3><ul>{ai.recommendations.map((item) => <li key={item}>{item}</li>)}</ul></div></div><p className="muted">AI explains the deterministic assessment. It does not set the score or category.</p></div> : <p className="muted">{ai.error ?? "The AI explanation is unavailable. The deterministic assessment above remains authoritative."}</p>}</section>
      {limitations.length > 0 && <section className="warnings-panel full-width"><p className="eyebrow">LIMITATIONS</p><ul>{limitations.map((warning) => <li key={warning}>{warning}</li>)}</ul></section>}
    </div>
  );
}

export default App;
