# Exemplos de prescrição para demonstração

**Importante:** Todos os dados neste diretório são sintéticos e criados exclusivamente para demonstração da plataforma NexoVital AI. Nenhum dado real de paciente está presente.

## Finalidade

Estes exemplos demonstram o fluxo de detecção de alterações em prescrições:
1. Submeter uma primeira versão de prescrição via `POST /api/analyses/{id}/prescriptions`
2. Submeter uma segunda versão com alterações (medicamento incluído, removido, dose alterada, etc.)
3. Verificar os resultados gerados pelo worker (summary, findings, evidences)

## Como usar

```bash
# 1. Criar análise com modalidade PRESCRIPTIONS
curl -X POST http://localhost:8000/api/analyses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/auth/mock-login -H 'Content-Type: application/json' -d '{"role":"DOCTOR"}' | jq -r .access_token)" \
  -d '{"patient_id":"patient-001","modalities":["PRESCRIPTIONS"]}'

# 2. Submeter primeira versão
curl -X POST http://localhost:8000/api/analyses/<ANALYSIS_ID>/prescriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d @examples/prescriptions/version-1.json

# 3. Submeter segunda versão (com alterações)
curl -X POST http://localhost:8000/api/analyses/<ANALYSIS_ID>/prescriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d @examples/prescriptions/version-2.json

# 4. Aguardar worker processar e verificar resultado
curl http://localhost:8000/api/analyses/<ANALYSIS_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

## Limitações

- O sistema NÃO é um validador farmacológico completo
- NÃO realiza validação de interações medicamentosas, alergias ou contraindicações
- NÃO possui ontologia farmacológica (nomes de medicamentos não são normalizados)
- As regras de detecção são demonstrativas e NÃO substituem avaliação profissional
- Os intervalos de dose são exemplos e NÃO constituem recomendações clínicas
