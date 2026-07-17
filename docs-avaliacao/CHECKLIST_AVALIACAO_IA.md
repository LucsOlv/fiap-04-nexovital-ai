# Checklist objetivo para avaliação por IA

## 1. Identificação rápida

| Item | Valor verificável |
| --- | --- |
| Projeto | NexoVital AI |
| Natureza | Projeto demonstrativo acadêmico — Tech Challenge Fase 4 |
| Usuário | Médico, sem autenticação |
| Arquitetura | React + FastAPI + LangGraph síncrono |
| Modalidades | Vídeo, áudio, texto clínico, sinais vitais (CSV), medicamentos |
| Persistência | `localStorage` (chave `nexovital_patients`) no frontend; nenhuma no backend |
| Pacientes | 3 fixtures fictícias (`patient-altered`, `patient-healthy`, `patient-neuro-no-history`) |
| Saída | Score 0–100, nível NORMAL/ATENÇÃO/ALERTA, achados, correlações, limitações, causas, tratamentos, disclaimer |
| Telas | `/pacientes` (edição) e `/analise` (wizard 6 etapas + relatório 9 abas) |

## 2. Requisitos atendidos — verificações objetivas

| # | Verificação | Arquivo | O que procurar | Resultado esperado |
| --- | --- | --- | --- | --- |
| 1 | LangGraph existe | `backend/app/graph.py` | `StateGraph`, `add_node` ×6, `add_edge`, `compile()` | 6 nós no fluxo até `END` |
| 2 | API multimodal | `backend/app/api/analyze.py` | `@router.post("/api/analyze")`, `UploadFile`, `Form` | 6 campos multipart |
| 3 | Vídeo usa pose estimation | `backend/app/analyzers/video.py` | `YOLO("yolov8n-pose.pt")` | Modelo de pose real, não mock |
| 4 | Áudio usa Azure Speech | `backend/app/analyzers/audio.py` | `SpeechRecognizer`, `recognize_once()`, `pt-BR` | SDK oficial Azure |
| 5 | Texto usa Azure Language | `backend/app/analyzers/text.py` | `TextAnalyticsClient`, `analyze_sentiment`, `extract_key_phrases` | SDK oficial Azure |
| 6 | CSV detecta anomalias | `backend/app/analyzers/vitals.py` | `REFERENCE_RANGES`, `_check_trends`, `_check_zscore` | 3 métodos de detecção |
| 7 | Medicamentos comparados | `backend/app/analyzers/medications.py` | `added_names`, `removed_names`, `common_names` | Diff determinístico |
| 8 | Fusão gera nível | `backend/app/analyzers/fusion.py` | `WEIGHTS`, `risk_level`, thresholds 70/30 | NORMAL, ATENÇÃO ou ALERTA |
| 9 | Resumo IA estruturado | `backend/app/services/openrouter_client.py` | `SYSTEM_PROMPT`, `_validate_report_schema` | JSON com schema mínimo |
| 10 | Três pacientes | `frontend/src/fixtures/patients.ts` | `patient-altered`, `patient-healthy`, `patient-neuro-no-history` | 3 fixtures com dados distintos |
| 11 | Disclaimer não diagnóstico | `backend/app/schemas/analysis.py` | Campo `disclaimer` em `AnalysisResponse` | "NÃO constitui diagnóstico médico" |
| 12 | Health check | `backend/app/api/health.py` | `GET /api/health` | Flags `azure_speech`, `azure_language`, `openrouter` |
| 13 | Grafo compilado singleton | `backend/app/api/analyze.py` | `_graph = build_graph()`, `_graph.ainvoke(state)` | Compilação única, reuso |
| 14 | Fallback OpenRouter | `backend/app/graph.py` | `_validate_and_return`: `final_report` mínimo | Sistema funciona sem OpenRouter |
| 15 | Termos críticos transparentes | `backend/app/analyzers/critical_terms.py` | Lista comentada de 35 pares (termo, severidade) | Heurísticas auditáveis |

## 3. Requisitos parciais

- [ ] **Alerta automático**: classificação visual (NORMAL/ATENÇÃO/ALERTA) existe na resposta e na tela com card colorido. Porém, entrega externa à equipe (e-mail, SMS, push, webhook) não existe. _Arquivos: `backend/app/analyzers/fusion.py`, `frontend/src/pages/AnalysisPage.tsx`_
- [ ] **Deploy Azure ativo**: templates Bicep (`infra/main.bicep`, `infra/modules/`) e CI/CD (`.github/workflows/deploy-azure.yml`) existem e compilam. Imagem backend é publicada no GHCR via `containers.yml`. Porém, deploy ativo em recurso Azure não foi comprovado. _Arquivos: `infra/`, `.github/workflows/`_
- [ ] **Áudio + Azure Language**: transcrição Azure Speech é obtida, mas não é enviada ao Azure Language para análise de sentimento/frases-chave. Apenas texto clínico usa Language. _Arquivo: `backend/app/analyzers/audio.py`_
- [ ] **Caso neurológico sem histórico**: limitação geral de histórico existe (`has_history: false`). Porém, `previous_medications: []` (lista vazia) é tratado como baseline existente pelo analisador de medicamentos, não como ausência. _Arquivos: `backend/app/graph.py`, `backend/app/analyzers/medications.py`_
- [ ] **Evidência de mídia**: gravação/upload existe no frontend. Notas de roteiro existem em `demo-data/`. Mas não há arquivos demo binários (vídeo/áudio) no repositório. _Arquivos: `demo-data/`, `frontend/src/components/`_
- [ ] **Timestamp de eventos no vídeo**: achados de vídeo possuem tipo, detalhe, severidade e score, mas não registram timestamp explícito de cada evento nos findings. _Arquivo: `backend/app/analyzers/video.py`_

## 4. Requisitos não encontrados

- [ ] E-mail/SMS/push/webhook de alerta à equipe médica
- [ ] Confirmação ou auditoria de alerta
- [ ] Autenticação/autorização (fora do escopo declarado)
- [ ] Banco de dados e histórico de análises (fora do escopo declarado)
- [ ] Anonimização automática de dados
- [ ] Vídeo final de apresentação versionado no repositório
- [ ] Teste automatizado ponta a ponta com Azure, OpenRouter, YOLO e FFmpeg reais
- [ ] Mecanismo de negação clínica na análise de texto

## 5. Pontos fortes

1. Pipeline LangGraph real e fácil de localizar (`backend/app/graph.py` com 6 nós)
2. Cinco analisadores separados por modalidade, cada um em arquivo dedicado
3. Score determinístico (fusão) separado do texto gerativo (OpenRouter) — IA não decide risco
4. Limitações e modalidades ausentes aparecem explicitamente na resposta
5. Azure Speech e Azure Language usam SDKs oficiais (integração real, não simulada)
6. Vídeo usa modelo de pose real (YOLOv8n Pose), não valor fixo ou mock
7. CSV possui 3 métodos de detecção explicáveis e 10 testes dedicados
8. Três cenários acadêmicos versionados com dados sintéticos distintos
9. Escopo mantido enxuto: sem worker, fila, banco ou autenticação desnecessários
10. UI funcional: gravação/upload de mídia, relatório em 9 abas, gráfico de vitais
11. Infraestrutura Azure declarada em Bicep com free tier (F0) e CI/CD
12. Fallback graceful: sistema funciona parcialmente sem serviços externos

## 6. Áreas de atenção para o avaliador

1. **Sem notificação externa**: alerta automático não envia notificação à equipe médica
2. **Deploy não comprovado**: infraestrutura declarada mas sem prova de publicação ativa
3. **Sem mídia binária**: dados demo são apenas roteiros/notas textuais
4. **Testes externos ausentes**: Azure, OpenRouter e YOLO não são cobertos por testes
5. **Duração não validada**: backend configura mas não aplica limites de duração de mídia
6. **Fusão saturável**: bônus aditivos (+15, +10) podem saturar score em 100
7. **Sem negação clínica**: busca de termos por substring detecta "sem dor" como "dor"
8. **Tratamentos por IA**: possíveis tratamentos gerados pelo OpenRouter exigem disclaimer reforçado

## 7. Como validar execução

### Ambiente

```bash
cp .env.example .env
docker compose up --build
```

### Health check

```bash
curl http://localhost:8000/api/health
```

Resposta deve conter `status: "ok"` e flags `azure_speech`, `azure_language`, `openrouter` (booleanos).

### Testes locais

```bash
# Backend — 32 testes
uv run --directory backend pytest

# Frontend — 1 teste
npm --prefix frontend test -- --run

# Frontend — lint e build
npm --prefix frontend run lint
npm --prefix frontend run build
```

Estado observado em 17/07/2026: 32 testes backend passaram, 1 teste frontend passou, lint e build frontend passaram, Ruff passou.

## 8. Como validar a pipeline

1. Abra `backend/app/graph.py`
2. Confirme imports dos 5 analisadores + `generate_report`
3. Confirme 6 nós: `validate_input`, `prepare_context`, `analyze_modalities`, `fuse_evidence`, `generate_summary`, `validate_and_return`
4. Confirme `build_graph()` com `StateGraph`, `add_node` ×6, `set_entry_point`, `add_edge` ×6, `compile()`
5. Abra `backend/app/api/analyze.py`
6. Confirme singleton `_graph = build_graph()` (linha 25)
7. Confirme `await _graph.ainvoke(state)` dentro do endpoint
8. Confirme que resposta inclui todas as modalidades, limitações e disclaimer

## 9. Como validar cada cenário

### Paciente alterado (Carlos Mendes)

- Selecione `patient-altered`
- Use CSV `demo-data/patient-altered/vitals.csv` (SpO2 97→88, FR 16→28, FC 84→111)
- Use texto de `demo-data/patient-altered/sample-audio-transcript.txt` como apoio
- Informe mudança de medicamento (ex: Enalapril 10mg → 20mg)
- Envie mídia real curta se disponível
- Confira queda de SpO2 e aumento respiratório nos achados de vitais

### Paciente saudável (Ana Beatriz)

- Selecione `patient-healthy`
- Use `demo-data/patient-healthy/vitals.csv`
- Use texto sem termos críticos
- Mantenha medicamentos iguais ao histórico
- Confira ausência ou baixa quantidade de anomalias

### Paciente neurológico (Rafael Oliveira)

- Selecione `patient-neuro-no-history` (selo "Sem histórico")
- Não envie CSV histórico
- Informe texto sobre fraqueza/dormência
- Confira limitação "Paciente sem histórico clínico prévio" e "vitals" em `missing_modalities`
- Confira confiança reduzida (score com -10 pontos)

## 10. Como validar a saída final

- [ ] `risk_level` ∈ {NORMAL, ATENÇÃO, ALERTA}
- [ ] `score` ∈ [0, 100]
- [ ] `available_modalities` lista modalidades com dados enviados
- [ ] `missing_modalities` lista modalidades não enviadas
- [ ] Cada analisador presente tem `status`, `severity`, `score`, `findings`, `evidence`, `limitations`
- [ ] Falha externa aparece como `limitations` (não como erro HTTP)
- [ ] `risk_level` e `score` vêm da fusão determinística, não do OpenRouter
- [ ] `disclaimer` aparece na resposta: "NÃO constitui diagnóstico médico"
- [ ] `ai_report` contém `summary`, `correlations`, `review_points`, `limitations`
- [ ] Saída não é apresentada como diagnóstico

## 11. Palavras-chave para busca automática no código

`StateGraph`, `ainvoke`, `yolov8n-pose.pt`, `SpeechRecognizer`, `recognize_once`, `analyze_sentiment`, `extract_key_phrases`, `REFERENCE_RANGES`, `zscore`, `_check_trends`, `previous_medications`, `fuse_evidence`, `risk_level`, `WEIGHTS`, `OPENROUTER_API_KEY`, `F0`, `patient-neuro-no-history`, `has_history`, `disclaimer`, `AnalysisResponse`, `AnalyzerOutput`.

## 12. Regras de interpretação para o avaliador

1. Projeto demonstrativo acadêmico — não é sistema de produção hospitalar
2. Apoio à decisão médica — não substitui diagnóstico
3. Dados reais devem ser anonimizados
4. Resultado depende da qualidade dos dados de entrada
5. Ausência de dados não significa normalidade
6. "Alerta automático" = classificação visual na tela, não notificação externa
7. Código de integração Azure/OpenRouter comprova implementação, não disponibilidade do serviço
8. Bicep comprova infraestrutura declarada, não deploy ativo
9. Notas de vídeo/áudio comprovam roteiro sintético, não execução multimídia
10. Teste unitário comprova regra isolada, não fluxo externo ponta a ponta

Projeto demonstrativo acadêmico. Apoio à decisão médica. Não substitui diagnóstico. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.
