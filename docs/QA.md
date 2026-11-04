# QA e melhorias de uso — 03/11/2026

Este documento registra a rodada anterior. A rodada final, com proteção de concorrência, disponibilidade do modelo e 47 testes, está em [PORTFOLIO.md](PORTFOLIO.md).

A validação funcional manual no Microsoft Edge foi posteriormente confirmada pela usuária em 03/11/2026. A pendência foi encerrada no relatório final, distinguindo esse relato dos testes executados pelo assistente.

## Resultado

**26 testes de backend e 11 de frontend aprovados.** TypeScript e build Vite aprovados. API final respondendo com HTTP 200. Os testes de gravação usam um banco temporário; a rodada manual não importou nem alterou transações da base demonstrativa.

## Falhas encontradas e corrigidas

| Falha | Correção e evidência |
| --- | --- |
| Ordenação da central de alertas era ignorada | API aceita coluna e direção; regressões cobrem valor, score, data e ID nos dois sentidos. |
| Alterar filtros apagava o status selecionado | A tabela mantém o estado de status e ordenação; retorna à primeira página ao mudar o recorte. Teste de componente e navegação manual. |
| Resultados antigos podiam aparecer após falha na consulta | Consultas canceláveis descartam dados anteriores; teste verifica uma resposta bem-sucedida seguida de erro. |
| Não havia recuperação prática de erro | Mensagens distinguem conexão, servidor e validação; tabela, detalhes e relatórios oferecem nova tentativa. |
| Comparação descartava o período anterior quando o atual estava vazio | As janelas usam dias completos e são calculadas mesmo sem resultados no período atual. Dois testes de regressão. |
| Exportações podiam levar a uma página de erro JSON | Download no próprio contexto, com estado de geração e feedback de sucesso/erro. CSV baixado e inspecionado: cabeçalho, UTF-8 e decimal brasileiro. |
| CSV gerado não era adequado à abertura padrão no Excel brasileiro | Exportação com ponto e vírgula e vírgula decimal. Importador aceita também CSV com vírgula e ponto decimal. |
| Importador não limitava largura de planilhas nem detectava cabeçalhos repetidos | Limite de 50 colunas, fechamento do workbook e rejeição explícita de colunas duplicadas. |
| IDs com barras e datas extremas podiam criar registros difíceis de abrir ou analisar | IDs restritos a letras, números, hífen e sublinhado; datas entre 2000 e 2100; UF brasileira e valores finitos validados. |
| Arquivos inválidos consumiam vagas de pré-visualização | Prévias sem linhas válidas não reservam token. |
| Prévia de importação expunha identificadores técnicos e listava milhares de erros | Cabeçalhos em português, valores e datas formatados; até 20 erros visíveis, com indicação do restante. |
| Detalhes permitiam perder observações e fechavam sem feedback ao salvar | Guarda de alterações não salvas, botão desabilitado sem mudanças, contador, confirmação interna, feedback e recarga do histórico. Testes de cancelar e salvar. |
| Confirmação nativa bloqueou o controle da aba durante o teste | Substituída por diálogo acessível no site, com título, descrição, foco inicial em cancelar e suporte a Escape. Fluxo de descarte verificado no navegador. |
| Menu móvel oculto continuava exposto à navegação assistiva | Invisibilidade real quando fechado; foco restrito ao menu quando aberto, Escape e retorno ao controle de abertura. |
| Navegação perdia a página ao atualizar | URLs por seção e integração com o histórico do navegador; título acompanha a página. |
| Valores e rótulos ficavam pequenos ou cortados | Fontes maiores, cards adaptáveis, gráficos de categorias e variáveis com barras horizontais e filtros organizados em grade no celular. |
| Estado vazio mostrava gráficos sem conteúdo útil | Mensagem única com orientação para ajustar filtros; métricas zeradas coerentes. |
| Erros de renderização podiam deixar uma tela vazia | Tratamento no topo da aplicação com opção de atualizar. |
| Bundle único carregava todas as páginas | Páginas carregadas sob demanda. Build final: entrada de aproximadamente 165 kB e módulo de gráficos de 423 kB; sem aviso de chunk acima de 500 kB. |
| PDF cortava linhas arbitrariamente | Quebra por largura da página e numeração de páginas. Geração coberta por teste de endpoint. |

## Verificações manuais

- Dashboard, agrupamento semanal, tabela, ordenação de alertas, combinação de risco e status, detalhes, cancelamento e descarte de observação não salva.
- Busca sem resultados, mensagem vazia e recuperação usando “Limpar filtros”.
- Navegação pelas oito seções, incluindo métricas de modelos e parâmetros do detector.
- Pré-visualização de `docs/modelo.csv`, sem confirmar a gravação na base da usuária.
- Download CSV pela página de relatórios, seguido de inspeção do arquivo.
- Desktop com viewport de 1440 px e celular de 390 px: conteúdo sem transbordamento horizontal na página, menu e cards verificados. A tabela mantém rolagem horizontal própria.
- Capturas: [desktop](screenshots/qa-desktop.jpg) e [celular](screenshots/qa-mobile.jpg).

## Limites da rodada

Não é certificação de ausência de bugs, teste de carga, pentest ou auditoria WCAG completa. A geração de Excel/PDF e a persistência de análises foram verificadas em testes automatizados; o salvamento na base demonstrativa não foi usado como teste destrutivo. A inspeção visual concentrou-se no navegador disponível, em dois tamanhos. Segue sendo uma demonstração local sem autenticação ou requisitos de operação bancária real.

O adaptador Starlette/httpx dos testes ainda emite um aviso de depreciação, sem falhas. Os servidores permanecem disponíveis para uso local, conforme solicitado pela usuária.
