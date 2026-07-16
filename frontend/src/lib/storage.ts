import type { DemoPatient } from "@/lib/api";
import { DEMO_PATIENTS } from "@/fixtures/patients";

const PATIENTS_KEY = "nexovital_patients";

function clonePatient(patient: DemoPatient): DemoPatient {
  return {
    ...patient,
    previous_medications: patient.previous_medications.map((item) => ({ ...item })),
  };
}

function cloneDefaults(): DemoPatient[] {
  return DEMO_PATIENTS.map(clonePatient);
}

function normalizePatient(value: unknown): DemoPatient | null {
  if (!value || typeof value !== "object") return null;

  const patient = value as Record<string, unknown>;
  if (
    typeof patient.id !== "string" ||
    typeof patient.name !== "string" ||
    typeof patient.age !== "number" ||
    (patient.sex !== "M" && patient.sex !== "F") ||
    typeof patient.summary !== "string" ||
    typeof patient.notes !== "string" ||
    typeof patient.has_history !== "boolean" ||
    !Array.isArray(patient.previous_medications)
  ) {
    return null;
  }

  const previous_medications = patient.previous_medications
    .filter(
      (item): item is { name: string; dose: string; frequency: string } =>
        !!item &&
        typeof item === "object" &&
        typeof (item as Record<string, unknown>).name === "string" &&
        typeof (item as Record<string, unknown>).dose === "string" &&
        typeof (item as Record<string, unknown>).frequency === "string",
    )
    .map((item) => ({ ...item }));

  return {
    id: patient.id,
    name: patient.name,
    age: patient.age,
    sex: patient.sex,
    summary: patient.summary,
    notes: patient.notes,
    previous_medications,
    has_history: patient.has_history,
    vitals_csv: typeof patient.vitals_csv === "string" ? patient.vitals_csv : undefined,
  };
}

export function savePatients(patients: DemoPatient[]): void {
  localStorage.setItem(PATIENTS_KEY, JSON.stringify(patients));
}

export function restoreDemoPatients(): DemoPatient[] {
  const defaults = cloneDefaults();
  savePatients(defaults);
  return defaults;
}

export function loadPatients(): DemoPatient[] {
  try {
    const raw = localStorage.getItem(PATIENTS_KEY);
    if (!raw) return restoreDemoPatients();

    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length !== DEMO_PATIENTS.length) {
      return restoreDemoPatients();
    }

    const normalized = parsed.map(normalizePatient);
    if (normalized.some((item) => item === null)) {
      return restoreDemoPatients();
    }

    return normalized as DemoPatient[];
  } catch {
    return restoreDemoPatients();
  }
}
