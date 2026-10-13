# CicloApp

Aplicacao Flask para cadastro de dados do ciclo e envio de mensagens por e-mail. Em producao, a aplicacao roda em AWS Lambda, com URL HTTPS publica, DynamoDB sob demanda e Amazon SES.

## Desenvolvimento local

Na raiz do repositorio, no PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Para abrir o formulario localmente sem chamar a AWS:

```powershell
python script/lambda.py
```

Acesse `http://127.0.0.1:5000`. Para testar o cadastro e o envio de verdade, configure `AWS_REGION`, `AWS_PROFILE`, `DYNAMO_TABLE` e `SENDER_EMAIL` com recursos AWS existentes e use credenciais locais autorizadas. O SES exige que o remetente esteja verificado; em sandbox, os destinatarios tambem precisam estar verificados.

## Publicacao pela pipeline

O workflow `.github/workflows/ci-cd.yml` executa os testes e valida o template SAM em pull requests. Um push para `master` publica a stack `ciclo-app` depois que as validacoes passam. O deploy autentica na AWS por OIDC, sem chaves de acesso salvas no GitHub.

Antes do primeiro deploy:

1. Na AWS, habilite o provedor de identidade OIDC do GitHub (`token.actions.githubusercontent.com`) e crie uma role confiavel somente para `repo:PROPRIETARIO/REPOSITORIO:ref:refs/heads/master`, com audiencia `sts.amazonaws.com`.
2. Conceda a essa role permissao para publicar a stack CloudFormation, enviar os artefatos SAM ao S3, criar/atualizar a Lambda, a Function URL e a tabela DynamoDB, e criar/pass-role da role de execucao da Lambda.
3. No GitHub, crie os secrets do repositorio `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN` e `SES_SENDER_EMAIL`.
4. Verifique `SES_SENDER_EMAIL` no SES da mesma regiao e solicite acesso de producao do SES para enviar a destinatarios fora do sandbox.
5. Abra um pull request e, apos a aprovacao, faca merge em `master`. A URL publica aparecera no log do job de deploy.

A tabela e configurada com cobranca sob demanda e preservada quando a stack for removida. A Function URL e publica; antes de compartilhar, adicione protecoes contra envios automatizados e publique um aviso de privacidade adequado aos dados coletados.