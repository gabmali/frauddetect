# Validação local — 3 de novembro de 2026

Registro da implementação inicial. Para a rodada posterior com **37 testes**, correções e capturas, consulte [QA.md](QA.md).

- Python 3.12.14 e Node.js 24.22.1.
- Pytest: **12 testes aprovados** (geração reproduzível, regras, limites de score, histórico causal, treino temporal, inferência fora da amostra, API, paginação, importação, fórmulas, alertas persistidos, relatórios e reconfiguração).
- Vitest: **3 testes aprovados** (rótulo de risco, erro acessível e filtro).
- TypeScript e build Vite: aprovados.
- Auditoria npm após atualização de Vite/Vitest: **0 vulnerabilidades reportadas**.
- Navegador: dashboard carregado com indicadores provenientes da API; tabela, detalhes e filtro de alto risco verificados. O filtro retornou somente operações de alto risco.
- Base final regenerada com 20.000 operações e 500 clientes; verificada a presença das cinco regras nos cenários sintéticos.
- Banco e modelo ficam ignorados no Git. Nenhum repositório remoto foi criado ou publicado.

## Avisos conhecidos

O build informa um bundle JavaScript de aproximadamente 595 kB (166 kB gzip); carregamento sob demanda dos gráficos é uma melhoria futura. Starlette emite um aviso de depreciação do adaptador de testes httpx; os testes passam. Não houve uma auditoria completa de acessibilidade ou teste visual em todos os tamanhos de tela. Os breakpoints responsivos estão implementados.

O banco SQLite temporário dos testes usa conexão isolada e é encerrado ao final. Os testes não alteram o banco demonstrativo. Os servidores usados na validação foram encerrados; inicie com `scripts/start.ps1` ou os comandos do README.
