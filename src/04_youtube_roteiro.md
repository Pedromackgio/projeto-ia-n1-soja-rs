# Roteiro do vídeo (5 min) — Projeto Soja RS (N2)

> Carregar em um canal público do YouTube e colocar o link no relatório.

## Estrutura sugerida (0:00 → 5:00)

### 0:00–0:30 — Abertura
- Slide com: título do projeto, integrantes (nome + RA), professor, disciplina
  (Inteligência Artificial), curso (SI) e instituição (FCI / Mackenzie).
- Narração: "Este projeto aplica aprendizado de máquina para prever a
  produtividade da soja nos municípios do Rio Grande do Sul..."

### 0:30–1:15 — Problema
- Mapa do RS + gráfico `03_evolucao_rendimento.png`.
- Falar da variabilidade interanual e dos vales de 2005, 2012, 2022
  (eventos de La Niña).

### 1:15–2:30 — Uso da IA
- Opção escolhida: Framework (scikit-learn).
- Fundamentos aplicados: regressão supervisionada, engenharia de atributos,
  validação temporal (sem embaralhar safras), comparação com linhas de base,
  Ridge Regression, Random Forest, Gradient Boosting.
- Mostrar o arquivo `src/03_train_models.py` rapidamente.

### 2:30–3:45 — Solução / artefato
- Diagrama do pipeline: SIDRA/IBGE → NOAA/ONI → NASA POWER → features
  agrometeorológicas → modelos → indicador de risco.
- Mostrar `figuras/07_comparacao_modelos.png` (MAE e R² dos 3 modelos vs. baselines).
- Mostrar `figuras/10_importancia_rf.png` (quais variáveis mais pesam).
- Mostrar `figuras/11_matriz_risco.png` (classificação de risco de quebra).

### 3:45–4:30 — GitHub
- Abrir https://github.com/Pedromackgio/projeto-ia-n1-soja-rs
- Percorrer rapidamente: `README.md`, `dados/`, `notebooks/`, `src/`,
  `relatorio/`, `figuras/`.

### 4:30–5:00 — Conclusão
- "Os modelos de boosting superaram as linhas de base, mostrando que dados
  agrometeorológicos públicos fornecem sinal útil para antecipar quebras de
  safra. Limites: escala municipal e dependência da qualidade dos dados em
  grade." Agradecimentos.

## Dicas de produção
- Gravar no OBS Studio ou QuickTime (1080p).
- Usar fontes grandes nos slides (projetado em 1080p, legível em celular).
- Treinar a fala — 5 minutos é curto, cronometrar.
- Upload "não listado" se o grupo preferir restringir visibilidade mas
  precisa continuar acessível via link.
