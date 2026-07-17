# Exemplos de prescrição para demonstração

Todos os dados deste diretório são sintéticos. Nenhum dado real de paciente está presente.

## Finalidade

`version-1.json` representa medicamentos anteriores. `version-2.json` representa medicamentos atuais. Analisador detecta inclusão, remoção e alteração de dose ou frequência.

## Como usar

Endpoint atual recebe paciente e medicamentos em `multipart/form-data`:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F 'patient={"id":"demo","name":"Paciente fictício","age":40,"sex":"F","has_history":true,"previous_medications":[{"name":"Dipirona","dose":"500mg","frequency":"6/6h"}]}' \
  -F 'medications=[{"name":"Dipirona","dose":"1g","frequency":"8/8h"}]'
```

Também é possível copiar conteúdo dos JSONs para campo **Medicamentos atuais** da tela `/analise`, usando primeira versão como histórico do paciente.

## Limitações

- não valida interações, alergias ou contraindicações;
- não possui ontologia farmacológica;
- nomes não são normalizados;
- regras são demonstrativas;
- doses dos exemplos não constituem recomendação;
- resultado exige revisão médica e não constitui prescrição.
