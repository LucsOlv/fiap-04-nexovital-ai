# Guia de vídeo demonstrativo — até 15 minutos

## Preparação antes da gravação

- [ ] Iniciar API e frontend (`docker compose up --build` ou execução separada)
- [ ] Confirmar `GET /api/health` retorna `status: "ok"`
- [ ] Preparar credenciais Azure/OpenRouter (não exibir segredos na tela)
- [ ] Preparar um áudio real curto em português para demonstrar Azure Speech
- [ ] Preparar um vídeo real curto com uma pessoa principal e corpo visível
- [ ] Carregar CSVs de `demo-data/` para uso rápido
- [ ] Testar os três cenários antes de gravar (pelo menos o crítico)
- [ ] Manter aba do código aberta nos arquivos indicados (graph.py, analyzers/, fusion.py)
- [ ] Não usar dados pessoais reais; anonimizar qualquer dado clínico real
- [ ] Verificar que `ruff check .` passa e os 32 testes pytest passam

Se Azure ou OpenRouter estiver indisponível, mostrar a limitação retornada pela API. Não apresentar roteiro textual como transcrição Azure real.

## Roteiro cronometrado — 12 segmentos

### 1. 0:00–0:45 — Contexto e título

**Fala sugerida:**
> NexoVital AI é projeto demonstrativo acadêmico do Tech Challenge Fase 4. A solução apoia análise médica multimodal: vídeo, áudio, texto clínico, medicamentos e sinais vitais são processados em um único fluxo. O sistema não realiza diagnóstico nem substitui avaliação profissional.

**Mostrar:**
- Título do projeto
- Tela de pacientes (`/pacientes`) com os 3 cards

### 2. 0:45–1:45 — Escopo do MVP

**Mostrar:**
- Três pacientes fictícios (Carlos Mendes, Ana Beatriz, Rafael Oliveira)
- Ausência de tela de login (sem autenticação)
- Duas telas: Pacientes e Análise
- Botão "Restaurar casos de demonstração"
- Edição de paciente com persistência em `localStorage`

**Explicar:**
- Processamento síncrono (tudo em uma requisição HTTP)
- Sem banco de dados, fila ou worker
- Dados salvos apenas no navegador

### 3. 1:45–2:45 — Arquitetura

**Mostrar:**
- Diagrama Mermaid em `docs-avaliacao/ARQUITETURA.md`
- Ou desenhar na tela o fluxo: React → FastAPI → LangGraph → 5 analisadores → Fusão → OpenRouter

**Explicar o fluxo (7 passos):**
1. React coleta modalidades (multipart/form-data)
2. FastAPI recebe e valida (tamanho, MIME)
3. LangGraph coordena 6 nós em sequência
4. Azure Speech e Language processam fala/texto
5. Regras locais analisam vídeo (YOLOv8 Pose), vitais (Pandas) e medicamentos (diff)
6. Fusão determinística calcula score e nível
7. OpenRouter gera síntese textual (causas, tratamentos)

**Enfatizar:** OpenRouter não decide o nível de risco — a fusão determinística decide.

### 4. 2:45–3:30 — Execução e health check

**Mostrar terminal:**
```bash
docker compose up --build
curl http://localhost:8000/api/health
```

**Mostrar resposta:**
```json
{"status":"ok","environment":"local","integrations":{"azure_speech":true,"azure_language":true,"openrouter":true}}
```

**Ocultar chaves.** Se alguma flag estiver `false`, dizer: "esta integração depende de configuração externa e a análise ficará parcial nesta modalidade."

### 5. 3:30–6:00 — Paciente crítico: Carlos Mendes (ALERTA)

**Passo a passo na tela:**
1. Selecionar Carlos Mendes / `patient-altered` na tela de análise
2. Enviar vídeo real curto (ou demonstrar componente de gravação VideoRecorder)
3. Enviar/gravar áudio real com fala semelhante a `demo-data/patient-altered/sample-audio-transcript.txt`
4. Preencher texto clínico: "Paciente relata cansaço extremo e falta de ar nos últimos 3 dias. Piora ao caminhar."
5. Informar medicamentos atuais com alteração: Enalapril 20mg (era 10mg), Salbutamol 100mcg, Ipratrópio 20mcg
6. Enviar `demo-data/patient-altered/vitals.csv`
7. Clicar **Executar análise**

**Mostrar resultado:**
- Nível ALERTA e score elevado (card vermelho com gradiente)
- Transcrição Azure (se obtida)
- Métricas acústicas: silêncio, pausas
- Achados posturais do YOLO (se vídeo enviado)
- Sinais vitais: queda de SpO2 (97→88), aumento de FR (16→28), tendência de FC (84→111)
- Alteração de medicamento: Enalapril dose modificada
- Correlações entre modalidades
- Limitações listadas
- Disclaimer: "NÃO constitui diagnóstico médico"

**Fala honesta:**
> Estes achados são heurísticos e demonstrativos. O resultado depende do vídeo, áudio, credenciais externas e regras atuais. O alerta é uma classificação visual interna — o sistema não envia notificação externa à equipe médica.

### 6. 6:00–8:00 — Paciente saudável: Ana Beatriz (NORMAL)

**Passo a passo:**
1. Selecionar Ana Beatriz Silva / `patient-healthy`
2. Usar `demo-data/patient-healthy/vitals.csv` (sinais estáveis)
3. Usar áudio/texto sem sintomas críticos (ex: "Paciente relata boa evolução pós-cirúrgica, sem queixas")
4. Manter medicamento igual ao histórico (Dipirona 500mg)
5. Executar análise

**Mostrar:**
- Sinais vitais estáveis, dentro das faixas
- Nenhuma ou poucas anomalias detectadas
- Nível NORMAL (card verde)
- Modalidades e limitações

Se o score não for coerente com os dados apresentados, não ocultar — mostrar os achados e pesos usados pela fusão.

### 7. 8:00–9:30 — Paciente neurológico: Rafael Oliveira (sem histórico)

**Passo a passo:**
1. Selecionar Rafael Oliveira / `patient-neuro-no-history`
2. Mostrar selo "Sem histórico" na interface
3. Não enviar CSV histórico (ausência intencional)
4. Informar texto sobre fraqueza/dormência: "Paciente relata episódios de fraqueza e dormência em membros inferiores. Sem diagnóstico fechado."
5. Opcionalmente enviar mídia atual (vídeo/áudio)
6. Executar análise

**Mostrar:**
- `vitals` em `missing_modalities`
- Limitação: "Paciente sem histórico clínico prévio — análise parcial"
- Confiança reduzida (score com -10 pontos)
- Análise parcial — resultado depende dos achados atuais

Não prometer nível ATENÇÃO apenas pela ausência de histórico. O código reduz score em 10 pontos; os achados atuais determinam a classificação final.

### 8. 9:30–11:00 — Evidência técnica no código

**Abrir, nesta ordem (30–45 segundos cada):**

1. `backend/app/graph.py` — mostrar `StateGraph`, 6 nós (`add_node`), `compile()`, `ainvoke`
2. `backend/app/api/analyze.py` — mostrar endpoint `POST /api/analyze`, singleton `_graph`
3. `backend/app/analyzers/video.py` — mostrar `YOLO("yolov8n-pose.pt")` e heurísticas
4. `backend/app/analyzers/audio.py` — mostrar `SpeechRecognizer`, `pt-BR`
5. `backend/app/analyzers/text.py` — mostrar `TextAnalyticsClient`, `analyze_sentiment`
6. `backend/app/analyzers/vitals.py` — mostrar `REFERENCE_RANGES`, `_check_trends`, `_check_zscore`
7. `backend/app/analyzers/medications.py` — mostrar diff (added/removed/modified)
8. `backend/app/analyzers/fusion.py` — mostrar `WEIGHTS`, thresholds (70/30)
9. `backend/app/schemas/analysis.py` — mostrar `AnalysisResponse` e `disclaimer`

Não gastar tempo lendo código inteiro. Destacar símbolos principais.

### 9. 11:00–12:30 — Infraestrutura Azure e CI/CD

**Mostrar:**
- `infra/modules/cognitive-services.bicep` — `SpeechServices` F0, `TextAnalytics` F0
- `infra/modules/container-apps.bicep` — escala 0–1, secrets Azure/OpenRouter
- `infra/modules/static-web-app.bicep` — plano Free
- `.github/workflows/deploy-azure.yml` — OIDC login, validate, deploy com what-if
- `.github/workflows/containers.yml` — build e push no GHCR

**Declarar:**
> A infraestrutura está implementada no código. Os templates Bicep compilam e o CI/CD está configurado. O deploy ativo em Azure ainda precisa ser comprovado — os templates e workflows são a evidência de que a infraestrutura foi planejada e codificada.

Se a aplicação estiver publicada e validada, mostrar URL e portal Azure sem expor segredos.

### 10. 12:30–14:00 — Testes e qualidade

**Mostrar comandos e resultados:**

```bash
# Backend: 32 testes passam
uv run --directory backend pytest
# → 32 passed, 1 warning

# Frontend: 1 teste passa
npm --prefix frontend test -- --run
# → 1 passed (AppLayout theme toggle)

# Lint e build
npm --prefix frontend run build
# → build concluído, chunk 581 kB

# Ruff: código limpo
uv run --directory backend ruff check .
# → All checks passed
```

**Mostrar distribuição dos testes:**
- `test_vitals.py` (10) — faixas, tendência, z-score
- `test_medications.py` (9) — adição, remoção, dose, frequência
- `test_fusion.py` (9) — ausência, convergência, escala
- `test_demo_patients.py` (2) — IDs esperados
- `test_health.py` (1) — status e flags
- `test_analyze.py` (1) — integração local com CSV e medicamentos reais

**Mostrar limitações principais:**
- Alerta externo não implementado (apenas classificação visual)
- Deploy Azure ativo ainda precisa comprovação
- Áudio não usa Azure Language sobre a transcrição
- Sem validade clínica (heurísticas demonstrativas)

### 11. 14:00–14:45 — Limitações e disclaimer

**Enumerar na tela (não ler todas, destacar as principais):**
1. Sistema demonstrativo — não validado clinicamente
2. Sem notificação externa à equipe médica
3. Heurísticas são proxies, não detectores clínicos
4. Sem banco de dados, sem histórico de análises, sem auditoria
5. Sem autenticação ou controle de acesso
6. Deploy Azure não comprovado
7. Dados demo não incluem mídia binária real
8. Possíveis causas/tratamentos gerados por IA exigem revisão profissional

### 12. 14:45–15:00 — Fechamento

**Fala sugerida:**
> O MVP demonstra entrada de cinco modalidades, orquestração LangGraph, Azure Speech, Azure Language, YOLOv8 Pose, detecção explicável de anomalias, comparação de medicamentos e relatório consolidado com causas e tratamentos. O escopo permanece acadêmico e demonstrativo. O resultado apoia a revisão médica, não constitui diagnóstico. Próximos passos incluem implementar notificação externa, comprovar deploy Azure, adicionar mídia binária aos dados demo e calibrar a fórmula de fusão.

Encerrar antes de 15:00.

## Plano alternativo — quando serviços externos falham

| Falha | Como demonstrar honestamente |
| --- | --- |
| Azure Speech indisponível | Mostrar `status`/`limitations` na resposta, código da integração e health flag `false`; não fabricar transcrição |
| Azure Language indisponível | Mostrar termos críticos locais funcionando e limitação "Azure AI Language não configurado" |
| OpenRouter indisponível | Mostrar score determinístico e resultados por modalidade; `ai_report.summary = "Relatório IA não disponível..."` |
| YOLO não baixa peso | Mostrar erro de modalidade e código; sugerir cache do peso para próxima tentativa |
| Sem vídeo real | Demonstrar componente de gravação/upload; declarar que análise de vídeo não foi validada nessa execução |
| Sem áudio real | Demonstrar gravação/upload; texto de roteiro não prova Speech to Text |
| Deploy Azure indisponível | Demonstrar local, Bicep compilado; não afirmar deploy concluído |

## Checklist de validação pós-gravação

- [ ] Duração menor que 15 minutos
- [ ] Áudio da narração compreensível
- [ ] Segredos (chaves API) não aparecem na tela
- [ ] Três pacientes mostrados (pelo menos um com análise completa)
- [ ] Pelo menos uma análise completa executada (preferencialmente o caso ALERTA)
- [ ] LangGraph mostrado no código (`graph.py`)
- [ ] Azure mostrado no health e/ou código
- [ ] Anomalias de CSV mostradas (tabela/gráfico)
- [ ] Medicamentos comparados (diff visível)
- [ ] Alerta visual mostrado (card colorido), sem chamar de "notificação externa"
- [ ] Limitações declaradas explicitamente
- [ ] Aviso não diagnóstico mostrado na tela
- [ ] Dados usados são fictícios ou anonimizados
- [ ] Código-fonte visível e navegável (não blurry)
- [ ] Terminal com resultado dos testes exibido

Projeto demonstrativo acadêmico. Apoio à decisão médica. Não substitui diagnóstico. Dados reais devem ser anonimizados. Resultado depende da qualidade dos dados de entrada.
