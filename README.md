# NexoVital AI

Demonstrativo acadêmico de apoio à análise médica multimodal.
MVP da Fase 4 do Tech Challenge.

> Especificação completa: [`NEXOVITAL_AI_MVP_SPEC.md`](NEXOVITAL_AI_MVP_SPEC.md).

```text
nexovital-ai/
├── frontend/            # React + TypeScript + Vite + Tailwind + shadcn/ui
├── backend/             # FastAPI + LangGraph + analisadores
├── demo-data/           # Fixtures dos 3 pacientes de demonstração
├── infra/               # Bicep mínimo (Static Web App, Container Apps, Speech, Language)
├── docs-avaliacao/      # Documentação completa para avaliação acadêmica (Fase 4)
└── examples/            # CSVs e prescrições de exemplo
```

## Pré-requisitos

- Node.js 22+
- Python 3.12+ e [uv](https://docs.astral.sh/uv/)
- Docker + Docker Compose
- FFmpeg (para processamento de vídeo/áudio)

## Instalação

```bash
# Backend
cd backend && uv sync

# Frontend
cd frontend && npm install
```

## Desenvolvimento local

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000 (health em `/api/health`)

## Testes

```bash
# Backend
cd backend && uv run pytest && uv run ruff check . && uv run mypy app

# Frontend
cd frontend && npm run build
```

## Infraestrutura

```bash
az bicep build --file infra/main.bicep
```

Detalhes em [`infra/README.md`](infra/README.md).

## Documentação de avaliação

A pasta [`docs-avaliacao/`](docs-avaliacao/) contém a documentação completa para avaliação acadêmica (Tech Challenge Fase 4):

| Arquivo | Conteúdo |
| --- | --- |
| [`EVIDENCIAS_DO_CODIGO.md`](docs-avaliacao/EVIDENCIAS_DO_CODIGO.md) | Inventário completo de evidências no código |
| [`MAPEAMENTO_REQUISITOS.md`](docs-avaliacao/MAPEAMENTO_REQUISITOS.md) | Requisitos do enunciado × implementação |
| [`ARQUITETURA.md`](docs-avaliacao/ARQUITETURA.md) | Diagramas e decisões arquiteturais |
| [`RELATORIO_TECNICO.md`](docs-avaliacao/RELATORIO_TECNICO.md) | Relatório técnico principal |
| [`README_AVALIACAO.md`](docs-avaliacao/README_AVALIACAO.md) | Guia rápido para banca avaliadora |
| [`CHECKLIST_AVALIACAO_IA.md`](docs-avaliacao/CHECKLIST_AVALIACAO_IA.md) | Checklist objetivo para IA avaliadora |
| [`GUIA_VIDEO_DEMONSTRACAO.md`](docs-avaliacao/GUIA_VIDEO_DEMONSTRACAO.md) | Roteiro de vídeo ≤15 minutos |

## Escopo do MVP

- 1 tipo de usuário (médico), sem autenticação
- 3 pacientes fictícios
- 2 telas (Pacientes e Análise)
- Análise síncrona via LangGraph
- Integrações reais: Azure Speech, Azure Language, OpenRouter, YOLOv8 Pose
- Nenhum banco de dados, worker, fila ou microserviço

Itens fora do escopo: ver §19 da especificação.
