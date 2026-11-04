# Publicação do FraudDetect

Código: https://github.com/gabmali/frauddetect

## Site público no GitHub Pages

**Abrir: https://gabmali.github.io/frauddetect/**

Qualquer pessoa pode acessar o site sem login, inclusive recrutadores. O link também aparece no início do README e no campo Website do repositório. Não é necessário usar o Render.

### Como funciona

O workflow `.github/workflows/pages.yml` publica automaticamente cada atualização da branch `main`:

1. Instala as dependências Python e gera 20.000 transações totalmente fictícias com semente fixa.
2. Calcula as regras causais, treina os modelos e exporta seus resultados com `python -m scripts.export_demo`.
3. Executa os testes do frontend e compila com `VITE_PAGES_DEMO=true`, `VITE_PUBLIC_DEMO=true` e `VITE_BASE_PATH=/frauddetect/`.
4. Publica os arquivos de `frontend/dist` usando GitHub Actions e GitHub Pages.

O GitHub Pages serve arquivos estáticos; o navegador calcula consultas e agregações a partir da base exportada. Não existe API Python hospedada nesse endereço. Os resultados dos modelos foram efetivamente calculados pelo código Python do projeto, durante o build.

### Recursos disponíveis

Dashboard, filtros combinados, agrupamentos, ordenação, paginação, detalhes, alertas para consulta, métricas de modelos, comparação de períodos e exportação CSV/Excel/PDF funcionam no navegador. Excel e PDF são carregados somente ao gerar esses formatos.

Importação e edição de regras ou análises estão desabilitadas na demonstração. Para usar esses recursos com persistência, siga a instalação local no README. O backend completo continua no repositório.

O JSON público contém somente dados fictícios. Não inclua credenciais, documentos ou transações reais no exportador. Nenhuma chave é necessária para o site.

### Atualizar e conferir

Depois de enviar alterações para `main`, acompanhe o workflow **Publicar site no GitHub Pages** na aba Actions. Aguarde os jobs `build` e `deploy` concluírem e então abra o endereço acima. O site usa navegação por hash, permitindo recarregar links como `/#modelos` sem erro de rota.

### Hospedagem opcional com backend

O `Dockerfile` e o `render.yaml` permanecem como alternativa para executar FastAPI e frontend juntos. Essa alternativa não é necessária para o GitHub Pages. As variáveis `PUBLIC_DEMO`, `REQUIRE_DEMO_AUTH`, `DEMO_ACCESS_USER` e `DEMO_ACCESS_PASSWORD` dizem respeito apenas à hospedagem com backend; não são usadas pela demonstração estática pública.

## Executar a imagem localmente

```sh
docker build -t frauddetect .
docker run --rm -p 10000:10000 frauddetect
```

Abra http://localhost:10000. O modo público é intencionalmente de consulta. Para utilizar todos os fluxos de edição, siga a instalação local do README.

Não versione bancos, arquivos `joblib`, logs ou `.env`. O envio ao GitHub não publica automaticamente o site: o deploy no serviço de hospedagem é uma etapa separada.

## Verificação da preparação

39 testes de backend e 15 de frontend aprovados; build público compilado. Os testes adicionais verificam o bloqueio de alterações no modo público e que somente a pasta do build é exposta pelo servidor. A imagem Docker ainda precisa ser construída e verificada pelo serviço de hospedagem; Docker não está instalado nesta máquina.

## Compartilhar com recrutadores

Envie o link HTTPS, o usuário e a senha diretamente aos recrutadores escolhidos. O endereço continua acessível pela internet, mas o conteúdo exige autenticação. A senha compartilhada pode ser repassada por quem a recebeu; altere-a no Render quando desejar revogar os acessos. O bloqueio de indexação é complementar e não substitui a autenticação.

Essa configuração protege o site hospedado. O repositório GitHub permanece público; torná-lo privado é uma decisão separada. O login da proprietária no Render continua necessário para criar e administrar a hospedagem. Recrutadores não precisam ter conta no Render.
