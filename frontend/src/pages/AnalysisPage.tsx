import { useState } from "react";

import AudioRecorder from "@/components/AudioRecorder";
import VideoRecorder from "@/components/VideoRecorder";
import VitalSignsChart from "@/components/VitalSignsChart";
import { Button } from "@/components/ui/button";
import type { AnalysisResult, AnalyzerOutput } from "@/lib/api";
import { submitAnalysis } from "@/lib/api";
import { loadPatients } from "@/lib/storage";
import { detectVitalAnomalies, parseVitalsCsv, validateVitalsCsv } from "@/lib/vitals";

// ── Tipos ──

interface MedicationItem { name: string; dose: string; frequency: string }
type VitalsPreset = "none" | "saudavel" | "taquicardico" | "infarto";
type FormTab = "paciente" | "video" | "audio" | "texto" | "medicamentos" | "vitais";
type ReportTab = "visao-geral" | "video" | "audio" | "texto" | "medicamentos" | "vitais" | "pontos" | "causas" | "tratamentos";
type TopTab = "form" | "result";

const VITALS_PRESETS: Record<string, { label: string; description: string; csv: string }> = {
  saudavel: { label: "Saudável", description: "Sinais normais", csv: `timestamp,heart_rate,systolic_bp,diastolic_bp,spo2,respiratory_rate,temperature
2026-07-16T09:00:00Z,72,118,78,98,16,36.5
2026-07-16T09:20:00Z,73,119,79,98,16,36.5
2026-07-16T09:40:00Z,71,117,77,99,15,36.6
2026-07-16T10:00:00Z,72,118,78,98,16,36.6
2026-07-16T10:20:00Z,74,120,80,98,16,36.5
2026-07-16T10:40:00Z,73,119,79,99,15,36.6
2026-07-16T11:00:00Z,72,118,78,98,16,36.5
2026-07-16T11:20:00Z,71,117,77,98,15,36.5
2026-07-16T11:40:00Z,72,118,78,99,16,36.6
2026-07-16T12:00:00Z,73,119,79,98,16,36.5` },
  taquicardico: { label: "Taquicárdico", description: "FC elevada", csv: `timestamp,heart_rate,systolic_bp,diastolic_bp,spo2,respiratory_rate,temperature
2026-07-16T09:00:00Z,95,132,84,97,17,36.7
2026-07-16T09:20:00Z,100,136,86,96,18,36.8
2026-07-16T09:40:00Z,105,138,88,95,19,36.8
2026-07-16T10:00:00Z,110,140,90,94,21,36.9
2026-07-16T10:20:00Z,115,142,92,93,22,37.0
2026-07-16T10:40:00Z,120,144,94,92,24,37.1
2026-07-16T11:00:00Z,122,146,95,91,25,37.1
2026-07-16T11:20:00Z,118,143,93,92,23,37.0
2026-07-16T11:40:00Z,125,148,96,90,26,37.2
2026-07-16T12:00:00Z,128,150,98,89,28,37.3` },
  infarto: { label: "Infarto", description: "IAM", csv: `timestamp,heart_rate,systolic_bp,diastolic_bp,spo2,respiratory_rate,temperature
2026-07-16T09:00:00Z,98,155,100,96,20,36.8
2026-07-16T09:20:00Z,105,160,102,95,22,36.9
2026-07-16T09:40:00Z,112,165,105,93,24,37.0
2026-07-16T10:00:00Z,118,170,108,91,26,37.1
2026-07-16T10:20:00Z,122,172,110,90,28,37.2
2026-07-16T10:40:00Z,126,175,112,88,29,37.3
2026-07-16T11:00:00Z,130,178,115,87,30,37.4
2026-07-16T11:20:00Z,132,180,116,86,31,37.5
2026-07-16T11:40:00Z,128,176,113,85,30,37.4
2026-07-16T12:00:00Z,135,182,118,84,32,37.6` },
};

const FORM_TABS: { key: FormTab; num: number; label: string; icon: string }[] = [
  { key: "paciente", num: 1, label: "Paciente", icon: "👤" },
  { key: "video", num: 2, label: "Vídeo", icon: "🎥" },
  { key: "audio", num: 3, label: "Áudio", icon: "🎤" },
  { key: "texto", num: 4, label: "Texto", icon: "📝" },
  { key: "medicamentos", num: 5, label: "Medicamentos", icon: "💊" },
  { key: "vitais", num: 6, label: "Sinais Vitais", icon: "🫀" },
];

const REPORT_TABS: { key: ReportTab; label: string; icon: string }[] = [
  { key: "visao-geral", label: "Visão Geral", icon: "📋" },
  { key: "video", label: "Vídeo", icon: "🎥" },
  { key: "audio", label: "Áudio", icon: "🎤" },
  { key: "texto", label: "Texto", icon: "📝" },
  { key: "medicamentos", label: "Medicamentos", icon: "💊" },
  { key: "vitais", label: "Sinais Vitais", icon: "🫀" },
  { key: "pontos", label: "Pontos Importantes", icon: "⚕" },
  { key: "causas", label: "Possíveis Causas", icon: "🔬" },
  { key: "tratamentos", label: "Tratamentos", icon: "💡" },
];

const nextTab: Record<FormTab, FormTab | null> = { paciente: "video", video: "audio", audio: "texto", texto: "medicamentos", medicamentos: "vitais", vitais: null };

// ── Helpers ──

const riskStyle: Record<string, { bg: string; text: string; border: string; dot: string; gradient: string }> = {
  NORMAL: { bg: "bg-emerald-50 dark:bg-emerald-950/40", text: "text-emerald-700 dark:text-emerald-300", border: "border-emerald-300 dark:border-emerald-800", dot: "bg-emerald-500", gradient: "from-emerald-400 to-emerald-500" },
  ATENÇÃO: { bg: "bg-amber-50 dark:bg-amber-950/40", text: "text-amber-700 dark:text-amber-300", border: "border-amber-300 dark:border-amber-800", dot: "bg-amber-500", gradient: "from-amber-400 to-orange-500" },
  ALERTA: { bg: "bg-red-50 dark:bg-red-950/40", text: "text-red-700 dark:text-red-300", border: "border-red-300 dark:border-red-800", dot: "bg-red-500", gradient: "from-red-500 to-red-600" },
};

const stepDescriptions: Record<FormTab, string> = {
  paciente: "Identificação e histórico",
  video: "Expressões e sinais visuais",
  audio: "Voz e sintomas relatados",
  texto: "Observações da consulta",
  medicamentos: "Prescrição atual",
  vitais: "CSV e tendências",
};

function sev(s: string) { const m: Record<string,string>={NORMAL:"Normal",ATENÇÃO:"Atenção",ALERTA:"Alerta"}; return m[s]??s; }
const modLabel: Record<string,string> = {video:"Vídeo",audio:"Áudio",text:"Texto clínico",vitals:"Sinais vitais",medications:"Medicamentos"};

// ── Página ──

export default function AnalysisPage() {
  const patients = loadPatients();
  const [formTab, setFormTab] = useState<FormTab>("paciente");
  const [patientId, setPatientId] = useState("");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [clinicalText, setClinicalText] = useState("");
  const [medications, setMedications] = useState<MedicationItem[]>([]);
  const [vitalsPreset, setVitalsPreset] = useState<VitalsPreset>("none");
  const [vitalsFile, setVitalsFile] = useState<File | null>(null);
  const [vitalsCsv, setVitalsCsv] = useState("");
  const [csvOk, setCsvOk] = useState<{ valid: boolean; warning?: string; dataRows: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [reportTab, setReportTab] = useState<ReportTab>("visao-geral");
  const [topTab, setTopTab] = useState<TopTab>("form");

  const sp = patients.find((p) => p.id === patientId);
  const filled: Record<FormTab, boolean> = { paciente: !!sp, video: !!videoFile, audio: !!audioFile, texto: !!clinicalText.trim(), medicamentos: medications.length > 0, vitais: !!vitalsFile || vitalsPreset !== "none" };

  function addM() { setMedications((p) => [...p, { name: "", dose: "", frequency: "" }]); }
  function upM(i: number, f: keyof MedicationItem, v: string) { setMedications((p) => p.map((m, j) => (j === i ? { ...m, [f]: v } : m))); }
  function rmM(i: number) { setMedications((p) => p.filter((_, j) => j !== i)); }

  function preset(p: VitalsPreset) { setVitalsPreset(p); setVitalsFile(null); setCsvOk(null); const csv = p === "none" ? "" : VITALS_PRESETS[p]?.csv ?? ""; setVitalsCsv(csv); if (csv) setCsvOk(validateVitalsCsv(csv)); }
  function onFile(f: File | null) { setVitalsFile(f); setVitalsPreset("none"); setCsvOk(null); setVitalsCsv(""); if (!f) return; const r = new FileReader(); r.onload = () => { const t = typeof r.result === "string" ? r.result : ""; setVitalsCsv(t); setCsvOk(validateVitalsCsv(t)); }; r.onerror = () => setCsvOk({ valid: false, dataRows: 0 }); r.readAsText(f); }

  function csvFile() { if (vitalsFile) return vitalsFile; if (vitalsPreset !== "none" && vitalsCsv) return new File([vitalsCsv], `${vitalsPreset}.csv`, { type: "text/csv" }); return null; }

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(""); setResult(null);
    if (!patientId) { setError("Selecione um paciente."); return; }
    const fd = new FormData();
    fd.append("patient", JSON.stringify(sp ?? {}));
    if (videoFile) fd.append("video", videoFile);
    if (audioFile) fd.append("audio", audioFile);
    if (clinicalText.trim()) fd.append("clinical_text", clinicalText.trim());
    if (medications.length > 0) fd.append("medications", JSON.stringify(medications));
    const c = csvFile(); if (c) fd.append("vitals_csv", c);
    setLoading(true);
    try { const d = await submitAnalysis(fd); setResult(d); setReportTab("visao-geral"); setTopTab("result"); }
    catch (err: unknown) { setError(err instanceof Error ? err.message : "Erro na análise."); }
    finally { setLoading(false); }
  }

  const parsedRecords = vitalsCsv ? parseVitalsCsv(vitalsCsv) : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-brand"><span className="h-2 w-2 rounded-full bg-brand" /> Central de análise</div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--app-text)]">Análise multimodal</h1>
          <p className="mt-1.5 app-text-muted">Colete sinais da consulta e revise achados em um único workspace.</p>
        </div>
        <div className="flex rounded-xl border app-border app-surface p-1 shadow-sm" role="tablist" aria-label="Modo da análise">
          <button type="button" role="tab" aria-selected={topTab === "form"} onClick={() => setTopTab("form")} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${topTab === "form" ? "bg-brand text-white shadow-sm" : "app-text-muted hover:text-[var(--app-text)]"}`}>Preenchimento</button>
          <button type="button" role="tab" aria-selected={topTab === "result"} onClick={() => setTopTab("result")} disabled={!result} className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${!result ? "cursor-not-allowed opacity-40" : topTab === "result" ? "bg-brand text-white shadow-sm" : "app-text-muted hover:text-[var(--app-text)]"}`}>Relatório {result && <span className="ml-1.5 rounded bg-[var(--app-surface)]/20 px-1.5 py-0.5 text-[11px]">{result.risk_level}</span>}</button>
        </div>
      </div>

      {topTab === "form" && (
        <form onSubmit={submit} className="grid gap-5 lg:grid-cols-[250px_minmax(0,1fr)]">
          <aside className="h-fit rounded-2xl border app-border app-surface p-3 shadow-sm lg:sticky lg:top-24">
            <div className="border-b app-border px-3 pb-3"><div className="text-xs font-bold uppercase tracking-wider app-text-muted">Fluxo da consulta</div><div className="mt-1 text-sm app-text-muted">{Object.values(filled).filter(Boolean).length} de {FORM_TABS.length} etapas</div></div>
            <div className="mt-3 space-y-1" role="tablist" aria-label="Etapas do preenchimento" aria-orientation="vertical">
              {FORM_TABS.map((t) => (
                <button key={t.key} type="button" role="tab" aria-selected={formTab === t.key} aria-current={formTab === t.key ? "step" : undefined} onClick={() => setFormTab(t.key)} className={`group flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition ${formTab === t.key ? "bg-brand text-white shadow-sm" : "app-text-muted hover:bg-[var(--app-surface-muted)] hover:text-[var(--app-text)]"}`}>
                  <span className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${formTab === t.key ? "bg-[var(--app-surface)]/20" : filled[t.key] ? "bg-emerald-500 text-white" : "bg-[var(--app-surface-muted)]"}`}>{filled[t.key] ? "✓" : t.num}</span>
                  <span className="min-w-0"><span className="block text-sm font-semibold">{t.label}</span><span className={`mt-0.5 block text-[11px] leading-4 ${formTab === t.key ? "text-white/75" : "app-text-muted"}`}>{stepDescriptions[t.key]}</span></span>
                </button>
              ))}
            </div>
            <div className="mt-4 rounded-xl app-surface-muted p-3 text-xs leading-5 app-text-muted"><strong className="app-text">Dica:</strong> complete etapas disponíveis. Análise funciona mesmo com modalidades ausentes.</div>
          </aside>

          <section className="min-w-0 rounded-2xl border app-border app-surface shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b app-border px-6 py-4 sm:px-8"><div><div className="text-xs font-semibold uppercase tracking-wider text-brand">Etapa {FORM_TABS.findIndex((t) => t.key === formTab) + 1} de {FORM_TABS.length}</div><div className="mt-1 text-lg font-bold text-[var(--app-text)]">{FORM_TABS.find((t) => t.key === formTab)?.label}</div></div><div className="text-xs app-text-muted">Campos marcados são processados com segurança local</div></div>
            <div className="min-h-[440px] p-6 sm:p-8 lg:p-10">
              {formTab === "paciente" && <PacienteTab patients={patients} patientId={patientId} setPatientId={setPatientId} sp={sp} />}
              {formTab === "video" && <MediaTab title="Vídeo" desc="Grave ou envie vídeo do paciente. Máx. 30s, 25MB — MP4, WebM, MOV." file={videoFile} setFile={setVideoFile} accept="video/mp4,video/webm,video/quicktime" recorder="video" />}
              {formTab === "audio" && <MediaTab title="Áudio" desc="Grave ou envie áudio da consulta. Máx. 2min, 10MB — WAV, MP3, M4A." file={audioFile} setFile={setAudioFile} accept="audio/*" recorder="audio" />}
              {formTab === "texto" && <div><h2 className="text-xl font-bold text-[var(--app-text)]">Texto clínico</h2><p className="mt-1.5 text-sm app-text-muted">Descreva sintomas, evolução e observações da consulta atual.</p><textarea className="mt-6 block w-full rounded-xl border app-border app-surface-muted px-5 py-4 text-sm text-[var(--app-text)] placeholder:app-text-muted focus:border-brand focus:bg-[var(--app-surface)] focus:ring-0 transition" rows={8} placeholder="Ex: Paciente relata cansaço aos mínimos esforços e falta de ar há 3 dias. Apresenta tosse seca. Sem febre. Dor torácica leve ao tossir." value={clinicalText} onChange={(e) => setClinicalText(e.target.value)} /></div>}
              {formTab === "medicamentos" && <div><h2 className="text-xl font-bold text-[var(--app-text)]">Medicamentos atuais</h2><p className="mt-1.5 text-sm app-text-muted">Liste os medicamentos prescritos nesta consulta. Serão comparados com o histórico.</p><div className="mt-6 space-y-2">{medications.length === 0 && <p className="text-sm italic app-text-muted">Nenhum medicamento adicionado.</p>}{medications.map((m, i) => <div key={i} className="flex flex-wrap gap-2"><input className="min-w-[180px] flex-1 rounded-lg border app-border app-surface-muted px-4 py-2.5 text-sm text-[var(--app-text)]" placeholder="Nome do medicamento" value={m.name} onChange={(e) => upM(i, "name", e.target.value)} /><input className="w-28 rounded-lg border app-border app-surface-muted px-3 py-2.5 text-sm text-[var(--app-text)]" placeholder="Dose" value={m.dose} onChange={(e) => upM(i, "dose", e.target.value)} /><input className="w-32 rounded-lg border app-border app-surface-muted px-3 py-2.5 text-sm text-[var(--app-text)]" placeholder="Frequência" value={m.frequency} onChange={(e) => upM(i, "frequency", e.target.value)} /><button type="button" className="px-2 app-text-muted hover:text-red-500" onClick={() => rmM(i)} aria-label={`Remover medicamento ${i + 1}`}>✕</button></div>)}</div><button type="button" className="mt-4 text-sm font-semibold text-brand hover:underline" onClick={addM}>+ Adicionar medicamento</button></div>}
              {formTab === "vitais" && <div><h2 className="text-xl font-bold text-[var(--app-text)]">Sinais vitais</h2><p className="mt-1.5 text-sm app-text-muted">Selecione um cenário pronto ou envie seu CSV.</p><div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{(["none","saudavel","taquicardico","infarto"] as VitalsPreset[]).map((p) => { const d = p === "none" ? { label: "Nenhum", description: "Sem CSV" } : VITALS_PRESETS[p]; return <button key={p} type="button" aria-pressed={vitalsPreset === p && vitalsFile === null} className={`rounded-xl border p-4 text-left text-sm transition ${vitalsPreset === p && vitalsFile === null ? "border-brand bg-brand/10 ring-2 ring-brand/20" : "app-border app-surface-muted hover:border-brand/50"}`} onClick={() => preset(p)}><div className="font-semibold text-[var(--app-text)]">{d.label}</div><div className="mt-1 text-xs app-text-muted">{d.description}</div></button>; })}</div><div className="mt-6 border-t app-border pt-5"><label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border app-border px-4 py-2.5 text-sm font-semibold app-text-muted hover:text-[var(--app-text)]">📁 Enviar CSV...<input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => onFile(e.target.files?.[0] ?? null)} /></label>{csvOk && <span className="ml-3 text-sm">{csvOk.valid ? <span className="text-emerald-600 dark:text-emerald-400">✓ {csvOk.dataRows} linhas</span> : <span className="text-red-600 dark:text-red-400">✕ Inválido</span>}{csvOk.warning && <span className="ml-2 text-amber-600 dark:text-amber-400">{csvOk.warning}</span>}</span>}</div>{parsedRecords.length > 0 && <div className="mt-5"><VitalSignsChart records={parsedRecords} anomalies={detectVitalAnomalies(parsedRecords)} /></div>}</div>}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-4 border-t app-border px-6 py-4 sm:px-8"><div className="text-xs app-text-muted">{filled[formTab] ? "Etapa preenchida" : "Etapa opcional"}</div><div className="flex gap-3">{nextTab[formTab] && <Button type="button" variant="outline" onClick={() => setFormTab(nextTab[formTab]!)}>Próxima etapa →</Button>}<Button type="submit" disabled={loading} className="min-w-[190px]">{loading ? <><Spinner /> Analisando...</> : "Executar análise"}</Button></div></div>
            {error && <div className="mx-6 mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300 sm:mx-8">{error}</div>}
          </section>
        </form>
      )}

      {topTab === "result" && result && <Report result={result} reportTab={reportTab} setReportTab={setReportTab} />}
    </div>
  );
}

// ── Sub-páginas do formulário ──

function PacienteTab({ patients, patientId, setPatientId, sp }: { patients: ReturnType<typeof loadPatients>; patientId: string; setPatientId: (v: string) => void; sp: ReturnType<typeof loadPatients>[0] | undefined }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[var(--app-text)]">Paciente</h2>
      <p className="mt-1 text-sm app-text-muted">Selecione um dos três pacientes de demonstração.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {patients.map((p) => (
          <button key={p.id} type="button" onClick={() => setPatientId(p.id)}
            className={`rounded-xl border p-4 text-left transition ${
              patientId === p.id ? "border-brand app-surface-muted ring-2 ring-brand/20" : "app-border hover:border-brand/50"}`}>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white">{p.name.charAt(0)}</span>
              <div>
                <div className="text-sm font-semibold text-[var(--app-text)]">{p.name}</div>
                <div className="text-xs app-text-muted">{p.age} anos · {p.sex === "M" ? "Masculino" : "Feminino"}</div>
              </div>
            </div>
            <p className="mt-3 text-xs app-text-muted line-clamp-2">{p.summary}</p>
            <div className="mt-2 flex gap-3 text-[11px] app-text-muted">
              <span>{p.previous_medications.length} meds anteriores</span>
              <span>Histórico: {p.has_history ? "sim" : "não"}</span>
            </div>
          </button>
        ))}
      </div>
      {sp && (
        <div className="mt-4 rounded-xl border app-border app-surface-muted p-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-sm font-bold text-white">{sp.name.charAt(0)}</span>
            <div>
              <div className="font-semibold text-[var(--app-text)]">{sp.name}</div>
              <div className="text-sm app-text-muted">{sp.age} anos · {sp.sex === "M" ? "Masculino" : "Feminino"}</div>
            </div>
          </div>
          <p className="mt-3 text-sm text-[var(--app-text)]">{sp.summary}</p>
          {sp.notes && <p className="mt-2 text-sm app-text-muted">{sp.notes}</p>}
        </div>
      )}
    </div>
  );
}

function MediaTab({ title, desc, file, setFile, accept, recorder }: { title: string; desc: string; file: File | null; setFile: (f: File | null) => void; accept: string; recorder: "video" | "audio" }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[var(--app-text)]">{title}</h2>
      <p className="mt-1 text-sm app-text-muted">{desc}</p>
      <div className="mt-6">
        {recorder === "video" ? <VideoRecorder onRecorded={setFile} /> : <AudioRecorder onRecorded={setFile} />}
      </div>
      <label className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-lg border app-border px-4 py-2.5 text-sm app-text-muted hover:border-slate-300 hover:text-[var(--app-text)] transition">
        📁 Selecionar arquivo...
        <input type="file" accept={accept} className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      {file && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
          ✓ {file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)
          <button type="button" className="ml-auto text-emerald-400 hover:text-red-500 transition" onClick={() => setFile(null)}>Remover</button>
        </div>
      )}
    </div>
  );
}

function Spinner() { return <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>; }

// ── RELATÓRIO ──

function Report({ result, reportTab, setReportTab }: { result: AnalysisResult; reportTab: ReportTab; setReportTab: (t: ReportTab) => void }) {
  const rs = riskStyle[result.risk_level] ?? riskStyle.NORMAL;

  return (
    <div className="mt-10">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[var(--app-text)]">Relatório da Análise</h2>
        <p className="mt-1 text-sm app-text-muted">Resultado da análise multimodal — uso acadêmico demonstrativo.</p>
      </div>

      {/* ── Score Card ── */}
      <div className={`rounded-2xl border ${rs.border} ${rs.bg} p-8`}>
        <div className="flex flex-wrap items-center gap-5">
          <div className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${rs.gradient} shadow-lg`}>
            <span className="text-2xl font-black text-white">{result.score}</span>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full border ${rs.border} bg-[var(--app-surface)] px-4 py-1 text-sm font-bold ${rs.text}`}>{result.risk_level}</span>
              <span className="text-2xl font-bold text-[var(--app-text)]">{result.score}/100</span>
            </div>
            <p className="mt-1.5 text-sm app-text-muted">{result.available_modalities.length} modalidades analisadas{result.missing_modalities.length > 0 ? ` · ${result.missing_modalities.length} ausentes` : ""}</p>
          </div>
        </div>
        {/* Score bar */}
        <div className="mt-5">
          <div className="flex justify-between text-xs font-medium app-text-muted"><span>NORMAL</span><span>ATENÇÃO</span><span>ALERTA</span></div>
          <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-[var(--app-surface)]/80">
            <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-500 transition-all duration-700" style={{ width: `${result.score}%` }} />
          </div>
        </div>
      </div>

      {/* ── Report Tabs ── */}
      <div className="mt-6 flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1.5">
        {REPORT_TABS.map((t) => (
          <button key={t.key} type="button" onClick={() => setReportTab(t.key)}
            className={`flex shrink-0 items-center gap-1.5 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
              reportTab === t.key ? "bg-[var(--app-surface)] text-[var(--app-text)] shadow-sm" : "app-text-muted hover:text-[var(--app-text)]"}`}>
            <span className="text-xs">{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      <div className="mt-4 rounded-2xl border bg-[var(--app-surface)] p-8 shadow-sm">
        {reportTab === "visao-geral" && <VisaoGeral result={result} />}
        {reportTab === "video" && <DetailPanel label="Vídeo" data={result.video} />}
        {reportTab === "audio" && <DetailPanel label="Áudio" data={result.audio} />}
        {reportTab === "texto" && <DetailPanel label="Texto clínico" data={result.text} />}
        {reportTab === "medicamentos" && <DetailPanel label="Medicamentos" data={result.medications} />}
        {reportTab === "vitais" && <VitalsPanel data={result.vitals} />}
        {reportTab === "pontos" && <PontosImportantes result={result} />}
        {reportTab === "causas" && <CausasTab result={result} />}
        {reportTab === "tratamentos" && <TratamentosTab result={result} />}
      </div>

      {/* Disclaimer fixo */}
      <div className="mt-6 rounded-xl border-2 border-red-200 bg-red-50 p-5 text-center">
        <p className="text-sm font-bold text-red-700">⚠ Resultado DEMONSTRATIVO — NÃO constitui diagnóstico médico</p>
        <p className="mt-1 text-xs text-red-600">Os achados devem ser interpretados por profissional de saúde qualificado. Nenhuma decisão clínica deve ser baseada neste relatório.</p>
      </div>
    </div>
  );
}

// ── Painéis do relatório ──

function VisaoGeral({ result }: { result: AnalysisResult }) {
  return (
    <div className="space-y-8">
      {/* Resumo IA */}
      {result.ai_report ? (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-[var(--app-text)]">Resumo clínico</h3>
          <p className="text-sm leading-relaxed text-[var(--app-text)]">{result.ai_report.summary}</p>
        </div>
      ) : <p className="text-sm italic app-text-muted">Resumo IA não disponível (OpenRouter).</p>}

      {/* Cards de modalidade */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-[var(--app-text)]">Achados por modalidade</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          {(["video","audio","text","medications","vitals"] as const).map((k) => {
            const d = result[k];
            const labels: Record<string,string> = {video:"🎥 Vídeo",audio:"🎤 Áudio",text:"📝 Texto clínico",vitals:"🫀 Sinais vitais",medications:"💊 Medicamentos"};
            if (!d) return <div key={k} className="rounded-xl border border-dashed app-border p-4 text-sm app-text-muted">{labels[k]} — Não disponível</div>;
            return (
              <div key={k} className="rounded-xl border p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[var(--app-text)]">{labels[k]}</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${riskStyle[d.severity]?.bg ?? "bg-slate-100"} ${riskStyle[d.severity]?.text ?? "app-text-muted"}`}>{sev(d.severity)} · {d.score}</span>
                </div>
                {d.findings.length > 0 ? (
                  <ul className="mt-3 space-y-1.5">{d.findings.slice(0, 3).map((f, i) => <li key={i} className="text-[13px] app-text-muted leading-relaxed">• {String(f.detail ?? f.description ?? "")}</li>)}</ul>
                ) : <p className="mt-2 text-[13px] app-text-muted">Nenhum achado.</p>}
              </div>
            );
          })}
        </div>
      </div>

      {/* Correlações resumidas */}
      {result.correlations.length > 0 && (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-[var(--app-text)]">Correlações</h3>
          <div className="space-y-3">{result.correlations.map((c, i) => (
            <div key={i} className={`rounded-xl border-l-4 p-4 ${c.type === "convergent" ? "border-l-red-500 bg-red-50" : "border-l-amber-500 bg-amber-50"}`}>
              <span className={`rounded px-2 py-0.5 text-[11px] font-medium ${c.type === "convergent" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{c.type === "convergent" ? "Convergente" : "Divergente"}</span>
              <p className="mt-1.5 text-sm text-[var(--app-text)]">{String(c.description ?? "")}</p>
            </div>
          ))}</div>
        </div>
      )}

      {/* Limitações + ausentes */}
      <div className="rounded-xl app-surface-muted p-5">
        {result.limitations.length > 0 && <div className="mb-3"><h4 className="text-sm font-semibold text-[var(--app-text)]">Limitações</h4><ul className="mt-1 space-y-0.5">{result.limitations.map((l,i)=><li key={i} className="text-[13px] app-text-muted">• {l}</li>)}</ul></div>}
        {result.missing_modalities.length > 0 && <p className="text-[13px] app-text-muted">Modalidades não enviadas: {result.missing_modalities.map((m) => modLabel[m] ?? m).join(", ")}.</p>}
      </div>
    </div>
  );
}

function DetailPanel({ label, data }: { label: string; data: AnalyzerOutput | null }) {
  if (!data) return <EmptyPanel label={label} />;
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--app-text)]">{label}</h3>
        <span className={`rounded-full px-3 py-1 text-sm font-medium border ${riskStyle[data.severity]?.border ?? ""} ${riskStyle[data.severity]?.bg ?? ""} ${riskStyle[data.severity]?.text ?? ""}`}>{sev(data.severity)} · Score {data.score}</span>
      </div>
      {data.findings.length === 0 && <p className="text-sm italic app-text-muted">Nenhum achado nesta modalidade.</p>}
      {data.findings.length > 0 && (
        <div className="space-y-3">{data.findings.map((f, i) => (
          <div key={i} className="rounded-xl border app-surface-muted p-4">
            <p className="text-sm text-[var(--app-text)]">{String(f.detail ?? f.description ?? JSON.stringify(f))}</p>
          </div>
        ))}</div>
      )}
      {data.evidence.length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium app-text-muted hover:text-[var(--app-text)]">Evidências técnicas</summary>
          <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-slate-100 p-4 text-xs app-text-muted">{JSON.stringify(data.evidence, null, 2)}</pre>
        </details>
      )}
      {data.limitations.length > 0 && <p className="mt-3 text-sm text-amber-600">⚠ {data.limitations.join("; ")}</p>}
    </div>
  );
}

function VitalsPanel({ data }: { data: AnalyzerOutput | null }) {
  if (!data) return <EmptyPanel label="Sinais vitais" />;
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--app-text)]">Sinais vitais</h3>
        <span className={`rounded-full px-3 py-1 text-sm font-medium border ${riskStyle[data.severity]?.border ?? ""} ${riskStyle[data.severity]?.bg ?? ""} ${riskStyle[data.severity]?.text ?? ""}`}>{sev(data.severity)} · Score {data.score}</span>
      </div>
      {data.findings.length > 0 && (
        <div className="mb-5 space-y-2">{data.findings.map((f, i) => <div key={i} className="rounded-xl border app-surface-muted p-4 text-sm text-[var(--app-text)]">{String(f.detail ?? f.description ?? JSON.stringify(f))}</div>)}</div>
      )}
      {data.evidence.length > 0 && (() => { const ev = data.evidence[0]; return <div className="flex gap-5 text-sm app-text-muted">{typeof ev.total_rows === "number" && <span>📊 {ev.total_rows} registros</span>}{typeof ev.anomaly_count === "number" && <span>⚠ {ev.anomaly_count} anomalias</span>}</div>; })()}
      {data.limitations.length > 0 && <p className="mt-3 text-sm text-amber-600">⚠ {data.limitations.join("; ")}</p>}
    </div>
  );
}

function PontosImportantes({ result }: { result: AnalysisResult }) {
  // Extrair todos os findings relevantes de todas as modalidades
  const allFindings: { modality: string; detail: string; severity: string }[] = [];
  const mods: { k: "video"|"audio"|"text"|"vitals"|"medications"; label: string }[] = [
    { k: "video", label: "Vídeo" }, { k: "audio", label: "Áudio" }, { k: "text", label: "Texto" },
    { k: "vitals", label: "Sinais vitais" }, { k: "medications", label: "Medicamentos" },
  ];
  for (const { k, label } of mods) {
    const d = result[k];
    if (!d) continue;
    for (const f of d.findings) {
      allFindings.push({ modality: label, detail: String(f.detail ?? f.description ?? ""), severity: String(f.severity ?? d.severity ?? "NORMAL") });
    }
  }

  // Separar por criticidade
  const criticos = allFindings.filter((f) => f.severity === "ALERTA");
  const atencao = allFindings.filter((f) => f.severity === "ATENÇÃO");

  // Gerar recomendações baseadas nos achados
  const recomendacoes: string[] = [];
  if (result.risk_level === "ALERTA") {
    recomendacoes.push("Avaliação médica imediata recomendada — múltiplos indicadores de alerta detectados.");
    if (result.vitals?.severity === "ALERTA") recomendacoes.push("Monitorar sinais vitais com frequência aumentada. Considere oximetria contínua e ECG.");
    if (result.video?.severity === "ALERTA") recomendacoes.push("Sinais de dor evidentes no vídeo — investigar origem da dor e considerar analgesia.");
    if (result.medications?.severity === "ALERTA") recomendacoes.push("Revisar alterações de prescrição recentes — possível necessidade de ajuste de dose.");
  } else if (result.risk_level === "ATENÇÃO") {
    recomendacoes.push("Avaliação clínica recomendada — alguns indicadores requerem atenção.");
    if (result.vitals?.severity === "ATENÇÃO") recomendacoes.push("Acompanhar evolução dos sinais vitais nas próximas horas.");
    if (result.video?.severity === "ATENÇÃO") recomendacoes.push("Observar evolução dos sinais de desconforto. Reavaliar em consulta de retorno.");
    recomendacoes.push("Solicitar exames complementares se houver piora clínica.");
  } else {
    recomendacoes.push("Paciente estável pelos critérios analisados. Manter acompanhamento de rotina.");
    recomendacoes.push("Nenhuma intervenção urgente identificada pelos indicadores atuais.");
  }
  if (result.missing_modalities.length > 0) {
    recomendacoes.push(`Completar avaliação com as modalidades ausentes: ${result.missing_modalities.map((m) => modLabel[m] ?? m).join(", ")}.`);
  }
  if (!result.ai_report) recomendacoes.push("Resumo IA indisponível — revisão manual dos achados é indispensável.");
  if (result.limitations.length > 0) recomendacoes.push("Análise possui limitações técnicas — interpretar resultados com cautela.");

  return (
    <div className="space-y-8">
      {/* Score summary */}
      <div className="flex items-center gap-6 rounded-xl app-surface-muted p-6">
        <div className="text-center">
          <div className={`text-3xl font-black ${riskStyle[result.risk_level]?.text ?? "app-text-muted"}`}>{result.score}</div>
          <div className="text-xs app-text-muted">Score</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-black text-[var(--app-text)]">{result.available_modalities.length}/{result.available_modalities.length + result.missing_modalities.length}</div>
          <div className="text-xs app-text-muted">Modalidades</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-black text-[var(--app-text)]">{criticos.length + atencao.length}</div>
          <div className="text-xs app-text-muted">Achados relevantes</div>
        </div>
      </div>

      {/* Achados críticos */}
      {criticos.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-red-700">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> Achados críticos
          </h3>
          <div className="space-y-3">{criticos.map((f, i) => (
            <div key={i} className="rounded-xl border-l-4 border-l-red-500 bg-red-50 p-4">
              <span className="text-[11px] font-medium uppercase text-red-400">{f.modality}</span>
              <p className="mt-1 text-sm text-[var(--app-text)]">{f.detail}</p>
            </div>
          ))}</div>
        </div>
      )}

      {/* Achados de atenção */}
      {atencao.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-amber-700">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> Pontos de atenção
          </h3>
          <div className="grid gap-3 sm:grid-cols-2">{atencao.map((f, i) => (
            <div key={i} className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <span className="text-[11px] font-medium uppercase text-amber-400">{f.modality}</span>
              <p className="mt-1 text-sm text-[var(--app-text)]">{f.detail}</p>
            </div>
          ))}</div>
        </div>
      )}

      {/* Recomendações ao médico */}
      <div>
        <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-[var(--app-text)]">
          <span className="text-lg">⚕</span> Recomendações ao médico
        </h3>
        <div className="space-y-3">{recomendacoes.map((r, i) => (
          <div key={i} className="flex gap-3 rounded-xl border app-border bg-[var(--app-surface)] p-4">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">{i + 1}</span>
            <p className="text-sm text-[var(--app-text)]">{r}</p>
          </div>
        ))}</div>
      </div>


      {/* Correlações */}
      {result.correlations.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold app-text-muted">CORRELAÇÕES MULTIMODAIS</h3>
          <div className="space-y-2">{result.correlations.map((c, i) => (
            <div key={i} className="rounded-lg border app-border app-surface-muted p-4 text-sm text-[var(--app-text)]">
              <span className={`mr-2 rounded px-2 py-0.5 text-[11px] font-medium ${c.type === "convergent" ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"}`}>{c.type === "convergent" ? "CONV" : "DIV"}</span>
              {String(c.description ?? "")}
            </div>
          ))}</div>
        </div>
      )}

      {/* Limitações + disclaimer técnico */}
      {(result.limitations.length > 0 || result.missing_modalities.length > 0) && (
        <div className="rounded-xl app-surface-muted p-5">
          <h3 className="text-sm font-semibold app-text-muted">LIMITAÇÕES TÉCNICAS</h3>
          <ul className="mt-2 space-y-1">{result.limitations.map((l,i)=><li key={i} className="text-[13px] app-text-muted">• {l}</li>)}</ul>
          {result.missing_modalities.length > 0 && <p className="mt-2 text-[13px] app-text-muted">Modalidades ausentes: {result.missing_modalities.map((m) => modLabel[m] ?? m).join(", ")}.</p>}
        </div>
      )}
    </div>
  );
}

function CausasTab({ result }: { result: AnalysisResult }) {
  const causas = result.ai_report?.possible_causes;
  if (!causas || causas.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <span className="text-4xl">🔬</span>
        <p className="mt-3 text-sm font-medium app-text-muted">Possíveis causas não disponíveis</p>
        <p className="mt-1 text-xs app-text-muted">O resumo IA não incluiu este campo ou o OpenRouter não está configurado.</p>
      </div>
    );
  }

  const urgencyColor: Record<string, string> = { alta: "border-l-red-500 bg-red-50", média: "border-l-amber-500 bg-amber-50", baixa: "border-l-slate-300 app-surface-muted" };
  const urgencyBadge: Record<string, string> = { alta: "bg-red-100 text-red-700", média: "bg-amber-100 text-amber-700", baixa: "bg-slate-200 app-text-muted" };

  return (
    <div>
      <h3 className="mb-1 text-lg font-semibold text-[var(--app-text)]">Possíveis causas</h3>
      <p className="mb-5 text-sm app-text-muted">Condições clínicas plausíveis baseadas na combinação dos achados. Não constitui diagnóstico.</p>
      <div className="grid gap-4">
        {causas.map((c, i) => (
          <div key={i} className={`rounded-xl border-l-4 p-5 ${urgencyColor[c.urgency] ?? "border-l-slate-300 app-surface-muted"}`}>
            <div className="flex items-center justify-between">
              <span className="text-base font-semibold text-[var(--app-text)]">{c.condition}</span>
              <span className={`rounded-full px-3 py-0.5 text-xs font-medium ${urgencyBadge[c.urgency] ?? ""}`}>
                Urgência: {c.urgency}
              </span>
            </div>
            <p className="mt-2 text-sm leading-relaxed app-text-muted">{c.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TratamentosTab({ result }: { result: AnalysisResult }) {
  const tratamentos = result.ai_report?.possible_treatments;
  if (!tratamentos || tratamentos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <span className="text-4xl">💡</span>
        <p className="mt-3 text-sm font-medium app-text-muted">Tratamentos não disponíveis</p>
        <p className="mt-1 text-xs app-text-muted">O resumo IA não incluiu este campo ou o OpenRouter não está configurado.</p>
      </div>
    );
  }

  const typeIcon: Record<string, string> = { exame: "🔬", medicamentoso: "💊", encaminhamento: "🏥", terapia: "🩺", monitoramento: "📊" };
  const typeLabel: Record<string, string> = { exame: "Exame", medicamentoso: "Medicamentoso", encaminhamento: "Encaminhamento", terapia: "Terapia", monitoramento: "Monitoramento" };

  return (
    <div>
      <h3 className="mb-1 text-lg font-semibold text-[var(--app-text)]">Possíveis tratamentos e encaminhamentos</h3>
      <p className="mb-5 text-sm app-text-muted">Sugestões baseadas nas causas identificadas. Não constitui prescrição médica.</p>
      <div className="grid gap-4 sm:grid-cols-2">
        {tratamentos.map((t, i) => (
          <div key={i} className="rounded-xl border bg-[var(--app-surface)] p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{typeIcon[t.type] ?? "📋"}</span>
              <span className="text-[11px] font-medium uppercase app-text-muted">{typeLabel[t.type] ?? t.type}</span>
            </div>
            <p className="text-sm font-semibold text-[var(--app-text)]">{t.intervention}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed app-text-muted">{t.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmptyPanel({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 app-text-muted">
      <span className="text-4xl">—</span>
      <p className="mt-3 text-sm font-medium">{label} não disponível</p>
      <p className="mt-1 text-xs">Modalidade não enviada nesta análise.</p>
    </div>
  );
}
