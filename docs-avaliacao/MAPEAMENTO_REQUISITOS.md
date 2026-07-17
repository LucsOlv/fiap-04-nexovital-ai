# Mapeamento de requisitos — Tech Challenge Fase 4

## Critérios de status

- **Atendido:** evidência executável encontrada no código.
- **Parcial:** parte relevante existe, mas falta trecho exigido, prova ponta a ponta ou robustez.
- **Planejado:** intenção/documentação existe sem entrega executável completa.
- **Não encontrado:** nenhuma evidência correspondente.

Requisitos extraídos do enunciado da Fase 4 e da especificação interna `NEXOVITAL_AI_MVP_SPEC.md`. Mapeamento verificado contra o código em 17/07/2026.

| Requisito do enunciado | Evidência no código | Arquivos relacionados | Status | Observação |
| --- | --- | --- | --- | --- |
| Análise de vídeo clínico | FFmpeg amostra vídeo a 2 FPS; YOLOv8 Pose extrai keypoints COCO; heurísticas geram achados e score 0–100 | `backend/app/analyzers/video.py`, `backend/pyproject.toml`, `frontend/src/components/VideoRecorder.tsx` | Atendido | Heurísticas demonstrativas, sem validação clínica; não retorna frames anotados |
| Padrões de movimentação | 8 indicadores: proteção corporal, mão-corpo, tensão dos ombros, inclinação da cabeça, postura antálgica, flexão dos cotovelos, agitação e imobilidade | `backend/app/analyzers/video.py` | Atendido | Foco em sinais posturais associados a dor/desconforto |
| Eventos fora do padrão no vídeo | achados possuem tipo, detalhe, severidade e score por frame processado | `backend/app/analyzers/video.py` | Parcial | Não registra timestamp explícito de cada evento nos findings |
| Análise de áudio | gravação/upload, normalização FFmpeg (WAV 16kHz mono), métricas acústicas (FFprobe), transcrição Azure e termos críticos locais | `frontend/src/components/AudioRecorder.tsx`, `backend/app/analyzers/audio.py` | Atendido | `recognize_once()` limita consultas longas; duração backend não é validada |
| Azure Speech to Text | `SpeechConfig`, `SpeechRecognizer`, `recognize_once`, idioma `pt-BR` | `backend/app/analyzers/audio.py`, `.env.example`, `infra/modules/cognitive-services.bicep` | Atendido | Depende de chave/região e serviço externo real |
| Alterações de fala | silêncio (FFmpeg silencedetect), pausas (>0.5s), ritmo (volume médio), termos críticos na transcrição | `backend/app/analyzers/audio.py` | Atendido | Métricas são proxies heurísticos, não detector clínico validado |
| Azure Text Analytics/Language | `analyze_sentiment` e `extract_key_phrases` no texto clínico | `backend/app/analyzers/text.py`, `.env.example`, `infra/modules/cognitive-services.bicep` | Atendido | Não aplicado à transcrição de áudio |
| Análise de texto clínico | 35 termos críticos locais (respiratórios, cardiovasculares, neurológicos, gerais e fala), sentimento e frases-chave via Azure | `backend/app/analyzers/text.py`, `backend/app/analyzers/critical_terms.py` | Atendido | Busca por substring; sem negação/temporalidade médica |
| Detecção de anomalias em sinais vitais | 3 métodos: faixas de referência, tendência linear (SpO2, FC, FR) e z-score (|z| > 2.5 com ≥10 pontos) | `backend/app/analyzers/vitals.py`, `frontend/src/lib/vitals.ts`, `frontend/src/components/VitalSignsChart.tsx` | Atendido | Faixas demonstrativas; regras frontend/backend divergem ligeiramente |
| Upload e validação de CSV | limite por tamanho (1 MB), timestamp obrigatório, coluna vital e limite de 500 linhas | `backend/app/api/analyze.py`, `backend/app/analyzers/vitals.py`, `frontend/src/lib/vitals.ts` | Atendido | Parser frontend suporta CSV simples; backend usa Pandas |
| Análise de prescrições/medicamentos | detecta adição, remoção, mudança de dose e mudança de frequência | `backend/app/analyzers/medications.py`, `frontend/src/pages/AnalysisPage.tsx` | Atendido | Sem interação medicamentosa ou base farmacológica |
| Ausência de histórico | `has_history: false` gera limitação; fusão reduz score em 10 pontos | `backend/app/graph.py`, `backend/app/analyzers/fusion.py`, `frontend/src/fixtures/patients.ts` | Parcial | Medicamentos usam lista vazia como baseline existente; analisador não recebe flag de histórico |
| Fusão multimodal | pesos (vitals 0.30, video 0.25, audio 0.20, text 0.15, medications 0.10), regras de convergência/divergência e score 0–100 | `backend/app/analyzers/fusion.py`, `backend/tests/test_fusion.py` | Atendido | Média ponderada com regras heurísticas adicionais |
| Pipeline LangGraph | `StateGraph(AnalysisState)`, 6 nós, arestas fixas, compilação singleton e `ainvoke` | `backend/app/graph.py`, `backend/app/state.py`, `backend/app/api/analyze.py` | Atendido | Fluxo linear, síncrono e sem worker |
| Geração de alerta automático | resposta contém `risk_level` e `score`; frontend apresenta card visual com gradiente por nível | `backend/app/analyzers/fusion.py`, `backend/app/schemas/analysis.py`, `frontend/src/pages/AnalysisPage.tsx` | Parcial | Classificação visual existe; notificação externa à equipe não existe |
| Alerta para equipe médica | nenhuma integração de e-mail, SMS, push, webhook ou sistema hospitalar | — | Não encontrado | Não confundir alerta visual com entrega de notificação |
| Resumo clínico por IA | OpenRouter recebe achados estruturados e exige JSON com schema mínimo (5 causas, 3 tratamentos) | `backend/app/services/openrouter_client.py`, `backend/app/graph.py` | Atendido | Depende de chave externa; fallback local gera relatório mínimo |
| Resultado final estruturado | Pydantic define modalidades, correlações, limitações, causas, tratamentos e disclaimer fixo | `backend/app/schemas/analysis.py`, `frontend/src/lib/api.ts` | Atendido | Possíveis tratamentos exigem revisão profissional |
| Três pacientes demonstrativos | crítico/alterado (Carlos Mendes), saudável (Ana Beatriz), neurológico sem histórico (Rafael Oliveira) | `frontend/src/fixtures/patients.ts`, `backend/app/api/demo_patients.py`, `demo-data/` | Atendido | Dados de mídia são roteiros/notas, não áudio/vídeo binário |
| Caso crítico (alterado) | CSV com SpO2 97→88, FR 16→28 e FC 84→111 em 11 registros; transcrição com falta de ar | `demo-data/patient-altered/vitals.csv`, `demo-data/patient-altered/sample-audio-transcript.txt` | Atendido | Resultado final não possui teste ponta a ponta com mídia real |
| Caso saudável | CSV estável e transcrição sem sintomas críticos | `demo-data/patient-healthy/vitals.csv`, `demo-data/patient-healthy/sample-audio-transcript.txt` | Atendido | Resultado `NORMAL` não possui teste ponta a ponta da API |
| Caso neurológico sem histórico | fixture define `has_history: false` e `previous_medications: []`; README descreve ausência de baseline | `demo-data/patient-neuro-no-history/README.md`, `frontend/src/fixtures/patients.ts` | Atendido | Não possui CSV; resultado depende de entrada atual |
| Azure free tier | Speech `F0`, TextAnalytics `F0`, Static Web Apps `Free`, Container Apps 0–1 réplica | `infra/modules/cognitive-services.bicep`, `infra/modules/static-web-app.bicep`, `infra/modules/container-apps.bicep` | Atendido | Template e parâmetros compilam; deploy ativo ainda precisa comprovação |
| Hospedagem frontend e backend | Bicep declara Static Web App + Container Apps; GHCR público; workflow manual de deploy | `infra/main.bicep`, `.github/workflows/containers.yml`, `.github/workflows/deploy-azure.yml` | Parcial | Configuração é reproduzível; publicação Azure ativa ainda não foi comprovada |
| Processamento síncrono | endpoint aguarda `_graph.ainvoke(state)`; sem filas/workers | `backend/app/api/analyze.py`, `backend/app/graph.py`, `docker-compose.yml` | Atendido | Adequado ao MVP e limites curtos de mídia |
| Relatório técnico | documentação técnica gerada com evidências rastreáveis | `docs-avaliacao/RELATORIO_TECNICO.md`, `docs-avaliacao/ARQUITETURA.md` | Atendido | Documento acompanha versão avaliada do código |
| Vídeo demonstrativo até 15 minutos | roteiro detalhado com 12 segmentos cronometrados | `docs-avaliacao/GUIA_VIDEO_DEMONSTRACAO.md` | Planejado | Arquivo final do vídeo não está no repositório |
| Validade clínica (disclaimers) | código contém disclaimers e comentários sobre heurísticas demonstrativas | `backend/app/schemas/analysis.py`, `backend/app/analyzers/critical_terms.py`, `frontend/src/pages/AnalysisPage.tsx` | Atendido | Sistema declara não diagnóstico |
| Anonimização de dados reais | recomendação documental nos arquivos de avaliação | `docs-avaliacao/README_AVALIACAO.md`, `docs-avaliacao/RELATORIO_TECNICO.md` | Planejado | Não existe mecanismo técnico de anonimização |
| Monitoramento multimodal | 5 modalidades integradas: vídeo, áudio, texto, sinais vitais e medicamentos | `backend/app/analyzers/`, `backend/app/graph.py`, `backend/app/api/analyze.py` | Atendido | Todas as modalidades têm analisador dedicado |
| Integração com serviços gerenciados Azure | Azure Speech (F0), Azure Language (F0), Static Web Apps, Container Apps | `infra/`, `backend/app/analyzers/audio.py`, `backend/app/analyzers/text.py` | Atendido | Código de integração existe; runtime depende de credenciais |

## Síntese

### Atendidos (21 requisitos)

- Entrada e análise das cinco modalidades (vídeo, áudio, texto, sinais vitais, medicamentos)
- Azure Speech to Text com SDK oficial
- Azure AI Language com SDK oficial
- LangGraph real com 6 nós e estado tipado
- Anomalias de CSV por 3 métodos (faixas, tendência, z-score)
- Comparação de medicamentos (added/removed/modified)
- Três cenários demonstrativos com dados sintéticos
- Resposta estruturada com Pydantic e disclaimer não diagnóstico
- Infraestrutura Azure declarada em Bicep (F0/Free)
- Processamento síncrono sem worker/fila
- Monitoramento multimodal com analisadores dedicados
- Gravação e upload de mídia no frontend
- Fallback quando serviços externos indisponíveis
- Termos críticos locais como heurísticas transparentes
- Validação de CSV com limites configuráveis

### Parciais (4 requisitos)

- **Eventos fora do padrão no vídeo**: achados existem mas sem timestamp explícito nos findings
- **Ausência de histórico (medicamentos)**: `has_history` não é propagado ao analisador de medicamentos; lista vazia é tratada como baseline existente
- **Alerta automático**: classificação visual existe na tela; notificação externa à equipe não existe
- **Hospedagem/deploy Azure**: templates compilam e CI/CD existe; deploy ativo não foi comprovado

### Planejados (2 requisitos)

- **Vídeo demonstrativo**: roteiro detalhado existe em `docs-avaliacao/GUIA_VIDEO_DEMONSTRACAO.md`; arquivo final não está versionado
- **Anonimização automática**: recomendada nos documentos, mas não implementada tecnicamente

### Não encontrados (1 requisito)

- **Envio automático de alerta à equipe médica**: nenhuma integração de e-mail, SMS, push, webhook ou sistema hospitalar

Projeto demonstrativo acadêmico. Apoio à decisão médica. Não substitui diagnóstico. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.
