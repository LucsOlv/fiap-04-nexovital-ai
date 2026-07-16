import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import type { DemoPatient } from "@/lib/api";
import { loadPatients, restoreDemoPatients, savePatients } from "@/lib/storage";

export default function PatientsPage() {
  const [patients, setPatients] = useState<DemoPatient[]>(() => loadPatients());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    savePatients(patients);
  }, [patients]);

  function handleEdit(id: string) {
    setEditingId(editingId === id ? null : id);
  }

  function handleFieldChange(id: string, field: keyof DemoPatient, value: unknown) {
    setPatients((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p)),
    );
  }

  function handleMedChange(
    patientId: string,
    index: number,
    field: "name" | "dose" | "frequency",
    value: string,
  ) {
    setPatients((prev) =>
      prev.map((p) => {
        if (p.id !== patientId) return p;
        const meds = [...p.previous_medications];
        meds[index] = { ...meds[index], [field]: value };
        return { ...p, previous_medications: meds };
      }),
    );
  }

  function addMedication(patientId: string) {
    setPatients((prev) =>
      prev.map((p) =>
        p.id === patientId
          ? { ...p, previous_medications: [...p.previous_medications, { name: "", dose: "", frequency: "" }] }
          : p,
      ),
    );
  }

  function removeMedication(patientId: string, index: number) {
    setPatients((prev) =>
      prev.map((p) =>
        p.id === patientId
          ? { ...p, previous_medications: p.previous_medications.filter((_, i) => i !== index) }
          : p,
      ),
    );
  }

  function handleRestore() {
    const defaults = restoreDemoPatients();
    setPatients(defaults);
    setEditingId(null);
    setMessage("Casos de demonstração restaurados.");
    setTimeout(() => setMessage(""), 3000);
  }

  return (
    <section aria-labelledby="patients-title">
      <div className="flex items-center justify-between">
        <div>
          <h1 id="patients-title" className="text-2xl font-semibold text-slate-900">
            Pacientes
          </h1>
          <p className="mt-1 text-slate-600">
            Três pacientes fictícios para demonstração. Edite os dados conforme necessário.
          </p>
        </div>
        <Button type="button" onClick={handleRestore} variant="default">
          Restaurar casos de demonstração
        </Button>
      </div>

      {message && (
        <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {patients.map((patient) => (
          <div
            key={patient.id}
            className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-900">{patient.name}</h2>
                <p className="text-sm text-slate-500">
                  {patient.age} anos · {patient.sex === "M" ? "Masculino" : "Feminino"}
                </p>
              </div>
              {!patient.has_history && (
                <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                  Sem histórico
                </span>
              )}
            </div>

            <p className="mt-3 text-sm text-slate-600 line-clamp-3">{patient.summary}</p>

            {editingId === patient.id ? (
              <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
                <label className="block text-xs font-medium text-slate-700">
                  Nome
                  <input
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                    value={patient.name}
                    onChange={(e) => handleFieldChange(patient.id, "name", e.target.value)}
                  />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs font-medium text-slate-700">
                    Idade
                    <input
                      type="number"
                      className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                      value={patient.age}
                      onChange={(e) => handleFieldChange(patient.id, "age", Number(e.target.value))}
                    />
                  </label>
                  <label className="block text-xs font-medium text-slate-700">
                    Sexo
                    <select
                      className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                      value={patient.sex}
                      onChange={(e) => handleFieldChange(patient.id, "sex", e.target.value)}
                    >
                      <option value="M">Masculino</option>
                      <option value="F">Feminino</option>
                    </select>
                  </label>
                </div>
                <label className="block text-xs font-medium text-slate-700">
                  Resumo clínico
                  <textarea
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                    rows={3}
                    value={patient.summary}
                    onChange={(e) => handleFieldChange(patient.id, "summary", e.target.value)}
                  />
                </label>
                <label className="block text-xs font-medium text-slate-700">
                  Observações
                  <textarea
                    className="mt-1 block w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                    rows={2}
                    value={patient.notes}
                    onChange={(e) => handleFieldChange(patient.id, "notes", e.target.value)}
                  />
                </label>

                {/* Medicamentos anteriores */}
                <fieldset>
                  <legend className="text-xs font-medium text-slate-700">
                    Medicamentos anteriores
                  </legend>
                  {patient.previous_medications.map((med, idx) => (
                    <div key={idx} className="mt-2 flex gap-2">
                      <input
                        className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
                        placeholder="Nome"
                        value={med.name}
                        onChange={(e) => handleMedChange(patient.id, idx, "name", e.target.value)}
                      />
                      <input
                        className="w-20 rounded border border-slate-300 px-2 py-1 text-xs"
                        placeholder="Dose"
                        value={med.dose}
                        onChange={(e) => handleMedChange(patient.id, idx, "dose", e.target.value)}
                      />
                      <input
                        className="w-24 rounded border border-slate-300 px-2 py-1 text-xs"
                        placeholder="Frequência"
                        value={med.frequency}
                        onChange={(e) => handleMedChange(patient.id, idx, "frequency", e.target.value)}
                      />
                      <button
                        type="button"
                        className="text-xs text-red-500 hover:text-red-700"
                        onClick={() => removeMedication(patient.id, idx)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                    onClick={() => addMedication(patient.id)}
                  >
                    + Adicionar
                  </button>
                </fieldset>

                <label className="flex items-center gap-2 text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={patient.has_history}
                    onChange={(e) => handleFieldChange(patient.id, "has_history", e.target.checked)}
                  />
                  Possui histórico prévio
                </label>
              </div>
            ) : (
              <button
                type="button"
                className="mt-4 text-sm text-brand hover:underline"
                onClick={() => handleEdit(patient.id)}
              >
                Editar
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
