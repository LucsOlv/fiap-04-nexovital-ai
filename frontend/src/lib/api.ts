const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// ── Tipos ──

export interface AnalyzerOutput {
  status: string;
  severity: string;
  score: number;
  findings: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
  limitations: string[];
}

export interface PossibleCause {
  condition: string;
  rationale: string;
  urgency: "baixa" | "média" | "alta";
}

export interface PossibleTreatment {
  intervention: string;
  rationale: string;
  type: "exame" | "medicamentoso" | "encaminhamento" | "terapia" | "monitoramento";
}

export interface AiReport {
  summary: string;
  correlations: Array<Record<string, unknown>>;
  review_points: string[];
  limitations: string[];
  possible_causes: PossibleCause[];
  possible_treatments: PossibleTreatment[];
}

export interface AnalysisResult {
  risk_level: string;
  score: number;
  available_modalities: string[];
  missing_modalities: string[];
  video: AnalyzerOutput | null;
  audio: AnalyzerOutput | null;
  text: AnalyzerOutput | null;
  vitals: AnalyzerOutput | null;
  medications: AnalyzerOutput | null;
  correlations: Array<Record<string, unknown>>;
  limitations: string[];
  ai_report: AiReport | null;
  disclaimer: string;
}

export interface MedicationItem {
  name: string;
  dose: string;
  frequency: string;
}

export interface DemoPatient {
  id: string;
  name: string;
  age: number;
  sex: "M" | "F";
  summary: string;
  notes: string;
  previous_medications: MedicationItem[];
  has_history: boolean;
  vitals_csv?: string;
}

// ── API calls ──

export function fetchHealth(): Promise<{ status: string; integrations: Record<string, boolean> }> {
  return fetch(`${API_BASE_URL}/api/health`).then((r) => r.json());
}

export function fetchDemoPatients(): Promise<DemoPatient[]> {
  return fetch(`${API_BASE_URL}/api/demo-patients`).then((r) => r.json());
}

export async function submitAnalysis(formData: FormData): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Erro ${res.status}`);
  }
  return res.json() as Promise<AnalysisResult>;
}
