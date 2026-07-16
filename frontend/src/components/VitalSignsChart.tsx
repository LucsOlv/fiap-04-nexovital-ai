import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { VitalAnomaly, VitalRecord } from "@/lib/vitals";

interface VitalSignsChartProps {
  records: VitalRecord[];
  anomalies: VitalAnomaly[];
}

function shortTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function anomalyVariant(severity: VitalAnomaly["severity"]): "secondary" | "warning" | "danger" {
  if (severity === "alta") return "danger";
  if (severity === "moderada") return "warning";
  return "secondary";
}

export default function VitalSignsChart({ records, anomalies }: VitalSignsChartProps) {
  if (records.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sinais vitais</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm app-text-muted">Sem série temporal disponível para esta análise.</p>
        </CardContent>
      </Card>
    );
  }

  const chartData = records.map((record) => ({
    ...record,
    label: shortTime(record.timestamp),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sinais vitais e anomalias</CardTitle>
        <p className="text-sm app-text-muted">
          Gráfico simples de tendência com tabela de apoio. Cores mantêm significado fixo por sinal.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border app-border p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[var(--app-text)]">Frequência cardíaca e SpO₂</h3>
              <div className="flex gap-3 text-xs app-text-muted">
                <span className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-600" /> FC
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-600" /> SpO₂
                </span>
              </div>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} domain={["dataMin - 3", "dataMax + 3"]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="heart_rate"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 6 }}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="spo2"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 6 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-lg border app-border p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[var(--app-text)]">Temperatura e FR</h3>
              <div className="flex gap-3 text-xs app-text-muted">
                <span className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 rounded-full bg-orange-600" /> Temp
                </span>
                <span className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> FR
                </span>
              </div>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} domain={["dataMin - 2", "dataMax + 2"]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke="#ea580c"
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 6 }}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="respiratory_rate"
                    stroke="#d97706"
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, fill: "#ffffff" }}
                    activeDot={{ r: 6 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto rounded-lg border app-border">
          <table className="min-w-full divide-y divide-[var(--app-border)] text-sm">
            <thead className="app-surface-muted">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">Horário</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">FC</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">SpO₂</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">FR</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">Temp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--app-border)] bg-[var(--app-surface)]">
              {records.map((record) => (
                <tr key={record.timestamp}>
                  <td className="px-4 py-3 text-slate-700">{shortTime(record.timestamp)}</td>
                  <td className="px-4 py-3 text-slate-700">{record.heart_rate ?? "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{record.spo2 ?? "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{record.respiratory_rate ?? "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{record.temperature ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-[var(--app-text)]">Anomalias detectadas</h3>
          {anomalies.length === 0 ? (
            <p className="text-sm app-text-muted">Nenhuma anomalia demonstrativa detectada.</p>
          ) : (
            <ul className="space-y-2">
              {anomalies.map((anomaly, index) => (
                <li
                  key={`${anomaly.signal}-${anomaly.timestamp}-${index}`}
                  className="rounded-lg border app-border p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={anomalyVariant(anomaly.severity)}>{anomaly.severity}</Badge>
                    <span className="text-sm font-medium text-[var(--app-text)]">{anomaly.label}</span>
                    <span className="text-sm text-slate-500">{shortTime(anomaly.timestamp)}</span>
                    <span className="text-sm text-slate-500">Valor: {anomaly.value}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">{anomaly.reason}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
