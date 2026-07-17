# Evidências do código — NexoVital AI

Este inventário lista somente caminhos encontrados no repositório durante inspeção fresca em 17/07/2026. Evidências distinguem código executável, dados sintéticos, infraestrutura declarativa e lacunas.

## Inventário completo

| Área | Arquivo | Evidência | Por que importa |
| --- | --- | --- | --- |
| Visão do projeto | `README.md` | declara MVP acadêmico, stack, execução, três pacientes e fluxo síncrono | contextualiza escopo real |
| Especificação interna | `NEXOVITAL_AI_MVP_SPEC.md` | define recorte, requisitos, casos e itens fora do escopo | registra intenção; não prova implementação isoladamente |
| Rotas frontend | `frontend/src/main.tsx` | rotas `/pacientes` e `/analise` | comprova duas telas reais |
| Tela de pacientes | `frontend/src/pages/PatientsPage.tsx` | três cards, edição, medicamentos e restauração | comprova gestão mínima sem CRUD/backend |
| Tela de análise | `frontend/src/pages/AnalysisPage.tsx` | formulário em seis etapas e relatório em nove abas | concentra fluxo principal da demo |
| Cliente API | `frontend/src/lib/api.ts` | `fetchHealth`, `fetchDemoPatients`, `submitAnalysis` | comprova contrato HTTP do frontend |
| Fixtures frontend | `frontend/src/fixtures/patients.ts` | `patient-altered`, `patient-healthy` e `patient-neuro-no-history` | comprova três cenários fictícios |
| Persistência frontend | `frontend/src/lib/storage.ts` | valida e salva pacientes em `localStorage` (chave `nexovital_patients`) | comprova ausência de DB e persistência local |
| Gravação de vídeo | `frontend/src/components/VideoRecorder.tsx` | `getUserMedia`, `MediaRecorder`, WebM, limite de 30 s/25 MB | comprova captura e upload |
| Gravação de áudio | `frontend/src/components/AudioRecorder.tsx` | `MediaRecorder`, conversão WAV, limite de 2 min/10 MB | comprova captura e preparação de áudio |
| WAV frontend | `frontend/src/lib/wav.ts` | codificação do áudio gravado para WAV | suporta envio compatível |
| CSV frontend | `frontend/src/lib/vitals.ts` | valida timestamp, colunas e 500 linhas; parse e anomalias locais | comprova pré-validação/visualização |
| Gráfico de vitais | `frontend/src/components/VitalSignsChart.tsx` | Recharts, tabela e lista de anomalias | evidencia apresentação dos sinais |
| App FastAPI | `backend/app/main.py` | CORS, handler global de exceções e três routers (`health`, `demo_patients`, `analyze`) | comprova API única sem auth/DB |
| Health | `backend/app/api/health.py` | flags de Azure Speech, Azure Language e OpenRouter | permite checar configuração sem expor chave |
| Pacientes API | `backend/app/api/demo_patients.py` | retorna exatamente três pacientes | evidencia fixtures também no backend |
| Endpoint principal | `backend/app/api/analyze.py` | `POST /api/analyze` multipart | comprova entrada multimodal real |
| Validação de upload | `backend/app/api/analyze.py` | limites de tamanho (25 MB vídeo, 10 MB áudio, 1 MB CSV) e lista MIME | reduz entradas inválidas |
| Chamada do grafo | `backend/app/api/analyze.py` | `_graph = build_graph()` singleton e `_graph.ainvoke(state)` | comprova execução LangGraph na API |
| Estado LangGraph | `backend/app/state.py` | `AnalysisState` (TypedDict) e `AnalyzerResult` (TypedDict) | define contrato entre nós |
| Pipeline LangGraph | `backend/app/graph.py` | `StateGraph`, seis nós, arestas fixas e `END` | principal evidência de orquestração |
| Modalidades ausentes | `backend/app/graph.py` | gera `status: "missing"` por modalidade não enviada | evita tratar ausência como evidência positiva |
| Sem histórico | `backend/app/graph.py` | adiciona limitação quando `has_history` é falso | suporta caso neurológico parcial |
| Análise de vídeo | `backend/app/analyzers/video.py` | FFmpeg 2 FPS e `YOLO("yolov8n-pose.pt")` via Ultralytics | comprova modelo de pose real |
| Padrões visuais | `backend/app/analyzers/video.py` | postura de proteção, mão-corpo, tensão dos ombros, inclinação da cabeça, postura antálgica, flexão dos cotovelos, agitação e imobilidade | comprova heurísticas de movimento/postura |
| Temporários de vídeo | `backend/app/analyzers/video.py` | `tempfile.mkdtemp` e `shutil.rmtree` no finally | demonstra não retenção intencional |
| Análise de áudio | `backend/app/analyzers/audio.py` | FFmpeg normalização (WAV 16kHz mono), FFprobe métricas, silêncio, pausas e ritmo | comprova processamento acústico local |
| Azure Speech | `backend/app/analyzers/audio.py` | `SpeechConfig`, `SpeechRecognizer`, `recognize_once()`, idioma `pt-BR` | comprova integração Speech to Text |
| Texto clínico | `backend/app/analyzers/text.py` | termos críticos locais e score (busca por substring) | garante análise mínima sem Azure |
| Azure Language | `backend/app/analyzers/text.py` | `TextAnalyticsClient`, `analyze_sentiment` e `extract_key_phrases` | comprova serviço Azure Language |
| Termos críticos | `backend/app/analyzers/critical_terms.py` | 35 pares (termo, severidade) — respiratórios, cardiovasculares, neurológicos, gerais e fala | evidencia explicabilidade e limitação |
| Anomalias CSV | `backend/app/analyzers/vitals.py` | `REFERENCE_RANGES`, `CRITICAL_THRESHOLDS`, tendência linear e z-score (|z| > 2.5) | comprova detecção de anomalias |
| Leitura CSV | `backend/app/analyzers/vitals.py` | Pandas, timestamp obrigatório, colunas reconhecidas e máximo de linhas configurável | comprova validação backend |
| Medicamentos | `backend/app/analyzers/medications.py` | comparação de nome, dose e frequência (added/removed/modified) | comprova análise de prescrições |
| Fusão | `backend/app/analyzers/fusion.py` | pesos por modalidade, convergência, divergência e regras heurísticas | comprova integração multimodal |
| Nível de risco | `backend/app/analyzers/fusion.py` | limiares: score >= 70 → ALERTA, >= 30 → ATENÇÃO, < 30 → NORMAL | gera alerta visual interno |
| Resumo IA | `backend/app/services/openrouter_client.py` | chamada OpenRouter Chat Completions com JSON schema | comprova síntese por modelo externo |
| Prompt clínico | `backend/app/services/openrouter_client.py` | sistema de 12 regras: proíbe diagnóstico, cruza sintomas com medicamentos, exige disclaimer | reduz apresentação indevida como diagnóstico |
| Validação do resumo | `backend/app/services/openrouter_client.py` | verifica campos obrigatórios e quantidades mínimas (5 causas, 3 tratamentos) | evita aceitar JSON estruturalmente incompleto |
| Fallback OpenRouter | `backend/app/services/openrouter_client.py` | 3 retries com backoff, fallback local quando não configurado | garante resposta mesmo sem serviço externo |
| Schema de saída | `backend/app/schemas/analysis.py` | Pydantic: `AnalyzerOutput`, `AiReport`, `AnalysisResponse` | comprova formato final |
| Disclaimer | `backend/app/schemas/analysis.py` | texto fixo declarando resultado demonstrativo, não diagnóstico | reforça uso acadêmico |
| Configuração | `backend/app/core/config.py` | variáveis Azure/OpenRouter e limites de mídia via Pydantic Settings | centraliza dependências externas |
| Variáveis exemplo | `.env.example` | 19 variáveis documentadas sem segredos | permite configuração reproduzível |
| Dependências backend | `backend/pyproject.toml` | FastAPI, LangGraph, Ultralytics, Pandas, Azure SDKs, httpx, Pydantic | comprova stack instalada |
| Dependências frontend | `frontend/package.json` | React 18, TypeScript, Vite, Tailwind CSS, React Router, Recharts | comprova stack de UI |
| Docker backend | `backend/Dockerfile` | Python 3.12, FFmpeg, uvicorn | empacota API e dependência multimídia |
| Docker frontend | `frontend/Dockerfile` | Node 22 e Vite dev server | permite execução da interface em Compose |
| Compose | `docker-compose.yml` | backend + frontend, sem worker/DB, hot reload | comprova arquitetura mínima local |
| Azure principal | `infra/main.bicep` | 4 módulos: Cognitive Services (Speech F0 + Language F0), Container Apps (0–1 réplica), Static Web Apps (Free), budget | comprova arquitetura declarada |
| Azure Cognitive | `infra/modules/cognitive-services.bicep` | `SpeechServices` F0 e `TextAnalytics` F0 | comprova intenção de free tier |
| Azure backend | `infra/modules/container-apps.bicep` | ingress, segredos Azure (Speech, Language, OpenRouter), probes e escala 0–1 | comprova hospedagem planejada da API |
| Azure frontend | `infra/modules/static-web-app.bicep` | plano Free | comprova hospedagem planejada da UI |
| Budget | `infra/modules/budget.bicep` | orçamento mensal e notificações de custo | controla custo acadêmico |
| Deploy workflow | `.github/workflows/deploy-azure.yml` | login OIDC, validação e deploy Bicep com what-if | automatiza infraestrutura |
| CI backend | `.github/workflows/python.yml` | uv, Ruff, mypy e pytest | pipeline de qualidade do backend |
| CI frontend | `.github/workflows/frontend.yml` | lint, format:check, test e build | evidência de pipeline frontend |
| CI containers | `.github/workflows/containers.yml` | build e push da imagem backend no GHCR | publicação automatizada de containers |
| Testes vitais | `backend/tests/test_vitals.py` | 10 testes: CSV, faixas, tendência, z-score e caso normal | comprova regras centrais |
| Testes medicamentos | `backend/tests/test_medications.py` | 9 testes: adição, remoção, dose, frequência e sem baseline | comprova comparação |
| Testes fusão | `backend/tests/test_fusion.py` | 9 testes: ausência, convergência, histórico e escala | comprova comportamento do fusion |
| Testes pacientes | `backend/tests/test_demo_patients.py` | 2 testes: três IDs esperados | comprova cenários backend |
| Teste health | `backend/tests/test_health.py` | 1 teste: status e flags de integração | comprova endpoint de saúde |
| Teste analyze | `backend/tests/test_analyze.py` | 1 teste: integração local POST com CSV e medicamentos reais | comprova fluxo principal sem mocks |
| Teste frontend | `frontend/src/components/AppLayout.test.tsx` | 1 teste: tema escuro e persistência | cobertura frontend mínima |
| Dados alterados | `demo-data/patient-altered/vitals.csv` | 11 registros com SpO2 97→88, FR 16→28 e FC 84→111 | cenário sintético crítico |
| Texto alterado | `demo-data/patient-altered/sample-audio-transcript.txt` | fala com cansaço e falta de ar | roteiro para áudio de demonstração |
| Notas de vídeo alterado | `demo-data/patient-altered/sample-video-notes.txt` | amplitude reduzida e assimetria esperada | orientação, não mídia executável |
| Dados saudáveis | `demo-data/patient-healthy/vitals.csv` | sinais estáveis | cenário de controle |
| Texto saudável | `demo-data/patient-healthy/sample-audio-transcript.txt` | fala sem sintomas críticos | roteiro de controle |
| Caso sem histórico | `demo-data/patient-neuro-no-history/README.md` | ausência de CSV, prescrição e baseline | comprova intenção do terceiro cenário |
| Exemplos de vitais | `examples/vital-signs/sample-vital-signs.csv` | CSV adicional de referência | auxilia teste manual |
| Exemplos de prescrição | `examples/prescriptions/version-1.json` e `version-2.json` | versões anterior e atual | auxilia comparação manual |

## Limitações e ausências identificadas

| Área | Busca/inspeção | Conclusão |
| --- | --- | --- |
| Notificação médica externa | API, serviços e frontend | não encontrado e-mail, SMS, push ou webhook clínico |
| Banco de dados | dependências, compose e backend | não encontrado |
| Worker/fila | estrutura real | não encontrado; workflow Python CI ainda referencia worker, mas projeto não o possui |
| Autenticação | rotas e middleware | não encontrado; fora do escopo declarado |
| Mídia demo binária | `demo-data/` | não há arquivos de áudio/vídeo, apenas texto/notas |
| PDF do enunciado | raiz do projeto | não encontrado; mencionado apenas em `NEXOVITAL_AI_MVP_SPEC.md` |
| Deploy Azure ativo | arquivos e outputs versionados | não comprovado |
| Anonimização automática | backend/frontend | não encontrado |
| Vídeo final de demonstração | repositório | não encontrado |
| Mecanismo de negação clínica no texto | `critical_terms.py` e `text.py` | busca por substring, sem análise de negação/temporalidade |

## Resultados de validação observados em 17/07/2026

| Comando | Resultado |
| --- | --- |
| `uv run --directory backend pytest` | 32 passaram, 1 warning (httpx deprecation) |
| `npm --prefix frontend test -- --run` | 1 passou (AppLayout theme toggle) |
| `npm --prefix frontend run build` | passou; chunk JS 581,31 kB |
| `npm --prefix frontend run lint` | passou |
| `uv run --directory backend ruff check .` | passou; all checks passed |
| `uv run --directory backend mypy app --strict` | não executável no ambiente Windows atual (bloqueio App Control em DLL do mypy) |
| `az bicep build --file infra/main.bicep --stdout` | passou |
| `az bicep build-params --file infra/parameters/demo.bicepparam --stdout` | passou |

## Leitura correta das evidências

- Código de integração comprova implementação, não disponibilidade do serviço durante banca.
- Bicep comprova infraestrutura declarada, não deploy ativo.
- Notas de vídeo/áudio comprovam roteiro sintético, não execução multimídia.
- Teste unitário comprova regra isolada, não fluxo externo ponta a ponta.
- Nível `ALERTA` na tela comprova alerta visual, não notificação à equipe.
- ruff passando significa que os 21 issues anteriormente reportados foram corrigidos.
- mypy não pôde ser executado nesta máquina por restrição de ambiente Windows; resultado não reflete qualidade do código.

Projeto demonstrativo acadêmico. Apoio à decisão médica. Não substitui diagnóstico. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.
