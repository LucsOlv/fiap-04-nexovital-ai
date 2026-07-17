# NexoVital AI — guia para avaliação

## 1. Resumo

NexoVital AI é projeto demonstrativo acadêmico do Tech Challenge — Fase 4. O MVP recebe dados clínicos multimodais — vídeo, áudio, texto, medicamentos e sinais vitais em CSV — e produz achados por modalidade, score determinístico (0–100), nível NORMAL, ATENÇÃO ou ALERTA, correlações e resumo textual gerado por IA.

Sistema oferece apoio à decisão médica. Não substitui diagnóstico, prescrição ou avaliação profissional. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.

## 2. Objetivo acadêmico e escopo

**Objetivo**: demonstrar pipeline multimodal explicável, síncrona e orquestrada por LangGraph, com integrações reais a Azure Cognitive Services e OpenRouter.

**Escopo real**:
- Um perfil conceitual: médico
- Sem autenticação ou autorização
- Três pacientes fictícios com dados sintéticos
- Duas telas: Pacientes (`/pacientes`) e Análise (`/analise`)
- Aplicação FastAPI única, sem banco, fila ou worker
- Persistência local dos pacientes no `localStorage` (chave `nexovital_patients`)
- Integrações condicionadas a credenciais externas

## 3. Stack verificada

| Camada | Tecnologias |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Recharts, shadcn/ui |
| Backend | Python 3.12+, FastAPI, Pydantic, LangGraph, httpx |
| Vídeo | FFmpeg, Ultralytics YOLOv8n Pose, NumPy |
| Áudio | FFmpeg/FFprobe, Azure Speech SDK |
| Texto | Azure AI Text Analytics/Language, 35 termos críticos locais |
| Sinais vitais | Pandas, regressão linear, z-score |
| Relatório IA | OpenRouter via HTTP (Chat Completions), modelo configurável |
| Infraestrutura | Docker Compose, Azure Bicep (Static Web Apps, Container Apps, Speech, Language) |
| Qualidade | Pytest (32 testes), Vitest (1 teste), ESLint, Ruff, mypy |

Dependências: `backend/pyproject.toml` e `frontend/package.json`.

## 4. Como executar

### Opção A — Docker Compose

Pré-requisitos: Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Acessos:
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`

### Opção B — execução separada

Pré-requisitos: Node.js 22+, Python 3.12+, `uv` e FFmpeg/FFprobe no `PATH`.

```bash
# Terminal 1 — Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

**Atenção**: `backend/app/core/config.py` aponta o arquivo `.env` para caminho `C:/DEV/fiap-04-final/backend/.env`. Em Docker Compose, variáveis vêm de `.env` da raiz. Fora do Docker, configurar variáveis no ambiente ou ajustar/copiar arquivo conforme ambiente local.

## 5. Variáveis de ambiente

Fonte: `.env.example` e `backend/app/core/config.py`.

| Variável | Uso | Padrão |
| --- | --- | --- |
| `CORS_ORIGINS` | origens aceitas pela API | `http://localhost:5173` |
| `LOG_LEVEL` | nível de log | `INFO` |
| `APP_ENV` | identificação do ambiente | `local` |
| `AZURE_SPEECH_KEY` | credencial Speech to Text | — |
| `AZURE_SPEECH_REGION` | região Speech | — |
| `AZURE_LANGUAGE_KEY` | credencial Azure AI Language | — |
| `AZURE_LANGUAGE_ENDPOINT` | endpoint Language | — |
| `OPENROUTER_API_KEY` | geração do resumo IA | — |
| `OPENROUTER_MODEL` | modelo OpenRouter | `google/gemini-flash-1.5` |
| `OPENROUTER_BASE_URL` | endpoint OpenRouter | `https://openrouter.ai/api/v1` |
| `OPENROUTER_TIMEOUT` | timeout HTTP (s) | `60.0` |
| `OPENROUTER_MAX_RETRIES` | tentativas de JSON válido | `3` |
| `VIDEO_MAX_BYTES` | limite de vídeo | `26214400` (25 MB) |
| `VIDEO_MAX_DURATION_SECONDS` | duração declarada (não aplicada no backend) | `30.0` |
| `AUDIO_MAX_BYTES` | limite de áudio | `10485760` (10 MB) |
| `AUDIO_MAX_DURATION_SECONDS` | duração declarada (não aplicada no backend) | `120.0` |
| `CSV_MAX_BYTES` | limite de CSV | `1048576` (1 MB) |
| `CSV_MAX_ROWS` | limite de linhas | `500` |
| `VITE_API_BASE_URL` | URL da API no frontend | `http://localhost:8000` |

Não versionar segredos.

## 6. Como testar o fluxo principal

1. Abra `/pacientes` e confirme três casos fictícios (Carlos Mendes, Ana Beatriz, Rafael Oliveira)
2. Abra `/analise`
3. Selecione um paciente
4. Envie ou grave vídeo e áudio, quando disponíveis
5. Preencha texto clínico (ex: "paciente relata cansaço e falta de ar")
6. Informe medicamentos atuais
7. Escolha preset de sinais vitais ou envie CSV (`demo-data/`)
8. Clique em **Executar análise**
9. Verifique score, nível, achados por modalidade, correlações, limitações e aviso não diagnóstico
10. Consulte `GET /api/health` para confirmar disponibilidade das integrações

Dados auxiliares ficam em `demo-data/`. Pastas contêm CSV e roteiros textuais, não arquivos reais de áudio/vídeo.

## 7. Onde está cada parte

| Parte | Arquivo(s) principal(is) |
| --- | --- |
| Telas e rotas | `frontend/src/main.tsx`, `frontend/src/pages/PatientsPage.tsx`, `frontend/src/pages/AnalysisPage.tsx` |
| Gravação/upload | `frontend/src/components/VideoRecorder.tsx`, `frontend/src/components/AudioRecorder.tsx` |
| Cliente API | `frontend/src/lib/api.ts` |
| API backend | `backend/app/api/analyze.py`, `backend/app/api/health.py`, `backend/app/api/demo_patients.py` |
| Pipeline LangGraph | `backend/app/graph.py` (6 nós), `backend/app/state.py` (estado) |
| Azure Speech | `backend/app/analyzers/audio.py` |
| Azure Language | `backend/app/analyzers/text.py` |
| Vídeo/YOLO | `backend/app/analyzers/video.py` |
| CSV/anomalias | `backend/app/analyzers/vitals.py` |
| Medicamentos | `backend/app/analyzers/medications.py` |
| Fusão e alerta | `backend/app/analyzers/fusion.py` |
| Resumo IA | `backend/app/services/openrouter_client.py` |
| Contrato de saída | `backend/app/schemas/analysis.py` |
| Configuração | `backend/app/core/config.py` |
| Infraestrutura Azure | `infra/main.bicep`, `infra/modules/*.bicep` |
| CI/CD | `.github/workflows/deploy-azure.yml`, `containers.yml`, `python.yml`, `frontend.yml` |

## 8. Matriz resumida de requisitos

| Requisito | Evidência no projeto | Status |
| --- | --- | --- |
| Análise de vídeo clínico | YOLOv8 Pose + 8 heurísticas em `backend/app/analyzers/video.py` | Atendido |
| Análise de áudio | FFmpeg + Azure Speech + métricas acústicas em `backend/app/analyzers/audio.py` | Atendido |
| Análise de texto clínico | 35 termos críticos + Azure Language em `backend/app/analyzers/text.py` | Atendido |
| Análise de medicamentos | Comparação de adição, remoção, dose e frequência | Atendido |
| Sinais vitais em CSV | Pandas + 3 métodos (faixas, tendência, z-score) | Atendido |
| LangGraph | 6 nós, fluxo linear, compilado, `ainvoke` | Atendido |
| Azure Speech to Text | SDK oficial; depende de chave e região | Atendido |
| Azure Text Analytics/Language | SDK oficial; depende de chave e endpoint | Atendido |
| Alerta automático | Score determinístico + nível na resposta/tela | Parcial |
| Notificação à equipe médica | Não há envio externo (e-mail, SMS, push, webhook) | Não encontrado |
| Três cenários | Fixtures frontend/backend + dados em `demo-data/` | Atendido |
| Deploy Azure | Templates Bicep + CI/CD existem; deploy ativo não comprovado | Parcial |
| Relatório técnico | Conjunto `docs-avaliacao/` (7 arquivos) | Atendido |
| Vídeo demonstrativo | Roteiro detalhado existe; arquivo final não versionado | Planejado |

**"Alerta automático"** significa classificação exibida ao médico na tela (NORMAL/ATENÇÃO/ALERTA). Não significa e-mail, SMS, push, integração hospitalar ou confirmação de recebimento.

## 9. Verificações executadas em 17/07/2026

- **Backend**: 32 testes pytest passaram (1 warning httpx), Ruff passou (all checks passed)
- **Frontend**: 1 teste Vitest passou, ESLint passou, build concluído (chunk JS 581,31 kB)
- **Bicep**: `main.bicep` e `demo.bicepparam` compilaram
- **mypy**: não executável no ambiente Windows atual (App Control bloqueia DLL)

## 10. Avisos de uso

- Projeto demonstrativo acadêmico
- Apoio à decisão médica; não substitui diagnóstico
- Heurísticas não representam protocolo clínico validado
- Possíveis causas e tratamentos vêm de modelo externo (OpenRouter) e exigem revisão profissional
- Dados reais devem ser anonimizados
- Resultado depende da qualidade dos dados de entrada e configuração dos serviços externos
- Ausência de dados não significa normalidade

Projeto demonstrativo acadêmico. Apoio à decisão médica. Não substitui diagnóstico. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.
