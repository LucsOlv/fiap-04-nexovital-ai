import type { DemoPatient } from "@/lib/api";

export const DEMO_PATIENTS: DemoPatient[] = [
  {
    id: "patient-altered",
    name: "Carlos Mendes",
    age: 58,
    sex: "M",
    summary:
      "Paciente com histórico de DPOC, apresentando piora respiratória recente. Relata cansaço e falta de ar nos últimos 3 dias.",
    notes:
      "Ex-tabagista. Internação prévia por exacerbação há 3 meses. Medicamento antihipertensivo alterado recentemente. Caso preparado para ALERTA.",
    previous_medications: [
      { name: "Enalapril", dose: "10mg", frequency: "12/12h" },
      { name: "Salbutamol", dose: "100mcg", frequency: "6/6h" },
      { name: "Ipratrópio", dose: "20mcg", frequency: "6/6h" },
    ],
    has_history: true,
  },
  {
    id: "patient-healthy",
    name: "Ana Beatriz Silva",
    age: 34,
    sex: "F",
    summary:
      "Paciente em acompanhamento de rotina pós-cirúrgico. Sem queixas. Sinais vitais dentro da normalidade.",
    notes:
      "Apendicectomia há 30 dias. Retorno para liberação de atividades. Caso preparado para NORMAL.",
    previous_medications: [
      { name: "Dipirona", dose: "500mg", frequency: "6/6h (se dor)" },
    ],
    has_history: true,
  },
  {
    id: "patient-neuro-no-history",
    name: "Rafael Oliveira",
    age: 42,
    sex: "M",
    summary:
      "Paciente com quadro neurológico em investigação. Primeira consulta nesta unidade. Sem exames ou registros anteriores.",
    notes:
      "Encaminhado por neurologista. Episódios de fraqueza e dormência em membros inferiores. Caso preparado para ATENÇÃO parcial.",
    previous_medications: [],
    has_history: false,
  },
];
