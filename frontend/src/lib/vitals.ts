export interface VitalRecord {
  timestamp: string;
  heart_rate?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  spo2?: number;
  respiratory_rate?: number;
  temperature?: number;
}

export interface CsvValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
  dataRows: number;
  columns: string[];
}

export interface VitalAnomaly {
  signal: string;
  label: string;
  timestamp: string;
  value: number;
  severity: "leve" | "moderada" | "alta";
  reason: string;
}

const KNOWN_COLUMNS = [
  "heart_rate",
  "systolic_bp",
  "diastolic_bp",
  "spo2",
  "respiratory_rate",
  "temperature",
] as const;

function splitCsvLine(line: string): string[] {
  // ponytail: parser suporta CSV simples da demo sem aspas escapadas; trocar por parser completo se entrada real tiver vírgulas em valores.
  return line.split(",").map((value) => value.trim());
}

export function validateVitalsCsv(csv: string): CsvValidationResult {
  const lines = csv
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    return {
      valid: false,
      error: "CSV deve conter cabeçalho e ao menos uma linha de dados.",
      dataRows: 0,
      columns: [],
    };
  }

  const columns = splitCsvLine(lines[0]);
  if (!columns.includes("timestamp")) {
    return {
      valid: false,
      error: "CSV inválido: coluna obrigatória \"timestamp\" ausente.",
      dataRows: 0,
      columns,
    };
  }

  const vitalColumns = columns.filter((column) => KNOWN_COLUMNS.includes(column as (typeof KNOWN_COLUMNS)[number]));
  if (vitalColumns.length === 0) {
    return {
      valid: false,
      error: "CSV inválido: inclua ao menos uma coluna de sinal vital conhecida.",
      dataRows: lines.length - 1,
      columns,
    };
  }

  const dataRows = lines.length - 1;
  if (dataRows > 500) {
    return {
      valid: false,
      error: "CSV inválido: limite de 500 linhas excedido.",
      dataRows,
      columns,
    };
  }

  const unknownColumns = columns.filter((column) => column !== "timestamp" && !KNOWN_COLUMNS.includes(column as (typeof KNOWN_COLUMNS)[number]));

  return {
    valid: true,
    warning:
      unknownColumns.length > 0
        ? `Colunas ignoradas: ${unknownColumns.join(", ")}.`
        : undefined,
    dataRows,
    columns,
  };
}

function parseNumber(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function parseVitalsCsv(csv: string): VitalRecord[] {
  const validation = validateVitalsCsv(csv);
  if (!validation.valid) return [];

  const lines = csv
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const columns = splitCsvLine(lines[0]);

  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    const row = Object.fromEntries(columns.map((column, index) => [column, values[index] ?? ""])) as Record<string, string>;
    return {
      timestamp: row.timestamp,
      heart_rate: parseNumber(row.heart_rate),
      systolic_bp: parseNumber(row.systolic_bp),
      diastolic_bp: parseNumber(row.diastolic_bp),
      spo2: parseNumber(row.spo2),
      respiratory_rate: parseNumber(row.respiratory_rate),
      temperature: parseNumber(row.temperature),
    };
  });
}

export function detectVitalAnomalies(records: VitalRecord[]): VitalAnomaly[] {
  const anomalies: VitalAnomaly[] = [];

  records.forEach((record) => {
    if (typeof record.heart_rate === "number") {
      if (record.heart_rate < 50) {
        anomalies.push({
          signal: "heart_rate",
          label: "Frequência cardíaca",
          timestamp: record.timestamp,
          value: record.heart_rate,
          severity: "moderada",
          reason: "Bradicardia demonstrativa abaixo de 50 bpm.",
        });
      } else if (record.heart_rate > 120) {
        anomalies.push({
          signal: "heart_rate",
          label: "Frequência cardíaca",
          timestamp: record.timestamp,
          value: record.heart_rate,
          severity: "alta",
          reason: "Taquicardia demonstrativa acima de 120 bpm.",
        });
      } else if (record.heart_rate > 100) {
        anomalies.push({
          signal: "heart_rate",
          label: "Frequência cardíaca",
          timestamp: record.timestamp,
          value: record.heart_rate,
          severity: "leve",
          reason: "Frequência cardíaca acima da faixa esperada da demo.",
        });
      }
    }

    if (typeof record.spo2 === "number") {
      if (record.spo2 < 90) {
        anomalies.push({
          signal: "spo2",
          label: "SpO₂",
          timestamp: record.timestamp,
          value: record.spo2,
          severity: "alta",
          reason: "Saturação muito reduzida para critérios demonstrativos.",
        });
      } else if (record.spo2 < 94) {
        anomalies.push({
          signal: "spo2",
          label: "SpO₂",
          timestamp: record.timestamp,
          value: record.spo2,
          severity: "moderada",
          reason: "Saturação abaixo de 94% na série demonstrativa.",
        });
      }
    }

    if (typeof record.respiratory_rate === "number") {
      if (record.respiratory_rate > 24) {
        anomalies.push({
          signal: "respiratory_rate",
          label: "Frequência respiratória",
          timestamp: record.timestamp,
          value: record.respiratory_rate,
          severity: "alta",
          reason: "Taquipneia demonstrativa acima de 24 irpm.",
        });
      } else if (record.respiratory_rate > 20) {
        anomalies.push({
          signal: "respiratory_rate",
          label: "Frequência respiratória",
          timestamp: record.timestamp,
          value: record.respiratory_rate,
          severity: "leve",
          reason: "Frequência respiratória acima da faixa base da demo.",
        });
      }
    }

    if (typeof record.temperature === "number") {
      if (record.temperature >= 38.5) {
        anomalies.push({
          signal: "temperature",
          label: "Temperatura",
          timestamp: record.timestamp,
          value: record.temperature,
          severity: "alta",
          reason: "Febre alta demonstrativa.",
        });
      } else if (record.temperature >= 37.8) {
        anomalies.push({
          signal: "temperature",
          label: "Temperatura",
          timestamp: record.timestamp,
          value: record.temperature,
          severity: "moderada",
          reason: "Temperatura acima da faixa esperada da demo.",
        });
      }
    }

    if (typeof record.systolic_bp === "number") {
      if (record.systolic_bp >= 160 || record.systolic_bp <= 85) {
        anomalies.push({
          signal: "systolic_bp",
          label: "Pressão sistólica",
          timestamp: record.timestamp,
          value: record.systolic_bp,
          severity: "alta",
          reason: "Pressão sistólica fora da faixa demonstrativa.",
        });
      } else if (record.systolic_bp >= 140) {
        anomalies.push({
          signal: "systolic_bp",
          label: "Pressão sistólica",
          timestamp: record.timestamp,
          value: record.systolic_bp,
          severity: "leve",
          reason: "Pressão sistólica elevada para a demo.",
        });
      }
    }
  });

  const firstSpo2 = records.find((record) => typeof record.spo2 === "number")?.spo2;
  const lastSpo2 = [...records].reverse().find((record) => typeof record.spo2 === "number")?.spo2;
  if (typeof firstSpo2 === "number" && typeof lastSpo2 === "number" && firstSpo2 - lastSpo2 >= 4) {
    const lastRecord = records.length > 0 ? records[records.length - 1] : undefined;
    anomalies.push({
      signal: "spo2",
      label: "SpO₂",
      timestamp: lastRecord?.timestamp ?? records[0]?.timestamp ?? "",
      value: lastSpo2,
      severity: "alta",
      reason: "Queda progressiva de SpO₂ ao longo da série.",
    });
  }

  return anomalies;
}
