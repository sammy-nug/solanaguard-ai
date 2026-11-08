export interface RiskFinding { code: string; title: string; severity: string; kind: string; explanation: string; evidence: string[]; score_impact: number; program_id?: string | null; account?: string | null; }
export interface AnalysisResponse {
  transaction: { signature: string; network: string; status: string; slot?: number | null; fee?: number | null; warnings: string[] };
  analysis: { score: number; category: string; analysis_status: string; findings: RiskFinding[]; warnings: string[] };
  ai_explanation: { available: boolean; status: "available" | "unavailable"; summary?: string | null; transaction_purpose?: string | null; risk_explanation?: string | null; detected_issues: { code: string; explanation: string }[]; positive_indicators: string[]; recommendations: string[]; limitations: string[]; confidence_notes: string[]; error?: string | null };
}
interface ApiErrorResponse { error?: { message?: string } }
export async function analyzeTransaction(signature: string): Promise<AnalysisResponse> {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ signature }) });
  if (!response.ok) { const body = (await response.json().catch(() => null)) as ApiErrorResponse | null; throw new Error(body?.error?.message ?? `Analysis request failed with HTTP ${response.status}.`); }
  return response.json() as Promise<AnalysisResponse>;
}
