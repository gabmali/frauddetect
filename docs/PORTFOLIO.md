# FraudDetect — versão para apresentação

Validação de 3 de novembro de 2026. Projeto demonstrativo local, com dados inteiramente fictícios.

**Status: validação concluída para apresentação no portfólio local.** As verificações automatizadas e no navegador integrado foram complementadas pela validação manual no Microsoft Edge realizada e confirmada por Gabriela Oliveira em 03/11/2026.

## Correções finais

- Edições de alertas exigem a revisão recebida da API. O SQLite reserva a escrita antes de verificar essa revisão; alterações antigas retornam HTTP 409 e não sobrescrevem o registro. A interface preserva a observação local e oferece carregar a versão atual.
- Modelo ausente ou inválido gera aviso persistente, estado de saúde degradado e HTTP 503 nas operações que dependem de reavaliação. Classificações históricas continuam identificadas como o último processamento válido. Restaurar o artefato correspondente e verificar novamente remove o aviso.
- Parâmetros não salvos são protegidos ao navegar, voltar pelo histórico e fechar/recarregar a página. A navegação interna usa confirmação acessível.
- Relatórios foram conferidos por conteúdo: quantidade de linhas, período, risco, soma de valores, exposição, evolução, resumo Excel e texto/paginação do PDF. Há cobertura para período vazio.
- Contraste reforçado em botões, legendas, textos secundários, avatares e foco, preservando laranja e azul como cores da marca.

## Testes e evidências

Suíte ampliada: **32 testes de backend e 15 de frontend**. TypeScript e build de produção fazem parte da validação.

No navegador integrado, usando exclusivamente `data/portfolio-qa.db` e `data/portfolio-qa.joblib`, foram realizados:

1. Upload, prévia e confirmação de `docs/qa-import.csv`.
2. Recarga da página, busca da operação importada e conferência do score, risco e motivos.
3. Gravação de observação/status e nova recarga para confirmar persistência e histórico.
4. Edição do mesmo alerta em duas abas: uma gravação aceita, outra recusada, texto local preservado.
5. Edição de regras e tentativa de sair: cancelar mantém o valor; confirmar permite navegar.
6. Remoção temporária do modelo de QA: aviso visível; restauração e nova verificação recuperam o detector.

Capturas: [conflito de edição](screenshots/portfolio-conflito.jpg), [modelo indisponível](screenshots/portfolio-modelo-indisponivel.jpg), [dashboard](screenshots/qa-desktop.jpg) e [celular](screenshots/qa-mobile.jpg).

A base principal não recebeu as transações ou observações dos testes isolados executados pelo assistente. O teste manual posterior no Edge foi realizado pela usuária; a base e os arquivos utilizados nessa rodada não foram informados.

## Validação manual no Microsoft Edge

**Resultado: todos os itens do roteiro funcionaram, conforme confirmação da usuária.** Esta evidência é um relato de execução manual, não uma execução automatizada do assistente no Edge.

| Item do roteiro | Resultado informado |
| --- | --- |
| Abertura do site e carregamento do dashboard | Funcionou |
| Gráficos, agrupamentos e filtros | Funcionou |
| Busca sem resultados e limpeza dos filtros | Funcionou |
| Tabela, ordenação, paginação e detalhes | Funcionou |
| Central de alertas e preservação de observações ao cancelar | Funcionou |
| Salvamento e persistência após atualizar a página | Funcionou |
| Proteção de regras não salvas | Funcionou |
| Importação pelo roteiro fornecido | Funcionou |
| Relatórios CSV, Excel, PDF e página de Machine Learning | Funcionou |
| Janela estreita e navegação por teclado | Funcionou |

A versão exata do Edge, a versão do Windows e capturas dessa rodada não foram fornecidas. A pendência de validação funcional manual no Edge fica encerrada com base nesse relato. A tentativa anterior de automação do Edge permaneceu interrompida e não é contada como teste aprovado.

## Desempenho medido

Resultados nesta máquina, Python 3.12.14 / Windows 11; script reproduzível: `python -m scripts.benchmark`. Não são promessas de desempenho em outros equipamentos.

| Operações | Geração | Regras causais | Agregação |
| --- | ---: | ---: | ---: |
| 20.000 | 2,206 s | 0,660 s | 0,461 s |
| 100.000 | 8,858 s | 3,627 s | 1,068 s |

Essas medições são em memória e não incluem treino, consultas SQL ou carga concorrente. Dados completos: [benchmark.json](benchmark.json).

## Roteiro de apresentação — 5 minutos

1. Explique o objetivo: priorizar revisões, sem afirmar que alto risco comprova fraude.
2. Mostre o dashboard e aplique filtros de risco/período.
3. Abra uma transação e explique os pontos das regras e o indicador não calibrado do modelo.
4. Mostre a central de alertas, observações e histórico.
5. Compare Random Forest e regressão logística e explique precisão, recall e o corte temporal.
6. Demonstre a prévia de importação e exporte um relatório.
7. Apresente os testes, a arquitetura e as limitações dos dados sintéticos.

## Limites registrados

O navegador integrado foi verificado em tamanhos de desktop e celular; o roteiro funcional no Edge foi aprovado manualmente pela usuária, conforme registro acima. Firefox e Safari não foram verificados. Não foi realizada certificação WCAG, teste de carga distribuído ou pentest. O resultado permite apresentar o projeto como portfólio local, sem anunciar compatibilidade universal, ausência absoluta de falhas ou prontidão bancária de produção.

O aviso de depreciação Starlette/httpx nos testes continua sem causar falhas. Não há autenticação; mantenha os servidores em `127.0.0.1`.

Antes de publicar o repositório, substitua os espaços de GitHub, contato e demonstração pelos seus links reais. Nenhuma credencial, banco, modelo ou dado gerado deve ser versionado. O `.gitignore` já os exclui.
