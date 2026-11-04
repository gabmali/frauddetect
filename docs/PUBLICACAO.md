# Publicação do FraudDetect

Código: https://github.com/gabmali/frauddetect

## Demonstração restrita a recrutadores

O site pede usuário e senha antes de mostrar páginas, arquivos ou APIs. Somente o teste mínimo `/healthz` e a orientação de não indexação `/robots.txt` dispensam login. A ausência da senha mantém a demonstração fechada.

O repositório contém `Dockerfile` e `render.yaml` para publicar frontend e FastAPI juntos em um Web Service gratuito. Não utilize GitHub Pages para essa aplicação: ele não executa o backend Python.

1. Entre em https://dashboard.render.com e conecte sua conta GitHub.
2. Escolha **New → Blueprint** e selecione `gabmali/frauddetect`.
3. Confira o serviço `frauddetect`, runtime Docker e plano **Free**. Não habilite recursos pagos.
4. Defina `DEMO_ACCESS_PASSWORD` no painel do Render: use uma senha com pelo menos 16 caracteres. O usuário padrão é `recrutador`. Não coloque a senha no código, no README ou na URL.
5. Inicie o deploy. O endereço definitivo é atribuído pelo Render; não presuma que o subdomínio `frauddetect` estará disponível.
6. Abra a URL retornada e aguarde a inicialização dos dados e modelos.
7. Confira dashboard, busca, filtros, detalhes, métricas e relatórios. A versão pública bloqueia alterações; a versão local continua completa.
8. Coloque a URL verificada no início do README como **Demonstração para recrutadores — acesso com senha**, e no campo **Website** da seção About do GitHub.

O Render Free suspende o serviço após inatividade e pode levar cerca de um minuto para reativá-lo. O disco é efêmero: SQLite e modelo são recriados a partir dos dados fictícios quando necessário. Consulte as condições e limites atuais em https://render.com/docs/free. Não são necessários bancos reais, segredos da aplicação ou APIs pagas.

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
