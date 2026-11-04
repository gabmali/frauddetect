# Publicação do FraudDetect

Código: https://github.com/gabmali/frauddetect

## Hospedagem preparada no Render

O repositório contém `Dockerfile` e `render.yaml` para publicar frontend e FastAPI juntos em um Web Service gratuito. Não utilize GitHub Pages para essa aplicação: ele não executa o backend Python.

1. Entre em https://dashboard.render.com e conecte sua conta GitHub.
2. Escolha **New → Blueprint** e selecione `gabmali/frauddetect`.
3. Confira o serviço `frauddetect`, runtime Docker e plano **Free**. Não habilite recursos pagos.
4. Inicie o deploy. O endereço definitivo é atribuído pelo Render; não presuma que o subdomínio `frauddetect` estará disponível.
5. Abra a URL retornada e aguarde a inicialização dos dados e modelos.
6. Confira dashboard, busca, filtros, detalhes, métricas e relatórios. A versão pública bloqueia alterações; a versão local continua completa.
7. Coloque a URL verificada no início do README como **Acessar demonstração**, e no campo **Website** da seção About do GitHub.

O Render Free suspende o serviço após inatividade e pode levar cerca de um minuto para reativá-lo. O disco é efêmero: SQLite e modelo são recriados a partir dos dados fictícios quando necessário. Consulte as condições e limites atuais em https://render.com/docs/free. Não são necessários bancos reais, segredos da aplicação ou APIs pagas.

## Executar a imagem localmente

```sh
docker build -t frauddetect .
docker run --rm -p 10000:10000 frauddetect
```

Abra http://localhost:10000. O modo público é intencionalmente de consulta. Para utilizar todos os fluxos de edição, siga a instalação local do README.

Não versione bancos, arquivos `joblib`, logs ou `.env`. O envio ao GitHub não publica automaticamente o site: o deploy no serviço de hospedagem é uma etapa separada.

## Verificação da preparação

34 testes de backend e 15 de frontend aprovados; build público compilado. Os testes adicionais verificam o bloqueio de alterações no modo público e que somente a pasta do build é exposta pelo servidor. A imagem Docker ainda precisa ser construída e verificada pelo serviço de hospedagem; Docker não está instalado nesta máquina.
