# Gemini Assistant 3.1 Skill for Alexa

A reusable Alexa Custom Skill that sends spoken questions to the Google Gemini API. It includes English (`en-US`) and Brazilian Portuguese (`pt-BR`) interaction models and a Python AWS Lambda backend.

> **Security:** this repository does not contain an API key. You must create your own Google AI Studio key and provide it to Lambda as the `GOOGLE_API_KEY` environment variable. Never place a real key in GitHub, the interaction model, or the Alexa skill code.

## Features

- English and Brazilian Portuguese voice experiences.
- `ChatIntent` with an `AMAZON.SearchQuery` slot.
- Short, speech-friendly Gemini responses with Markdown cleanup.
- Conversation history limited to the current Alexa session.
- Timeout and API-error handling.
- No account-specific Lambda ARN in the source package.

## Project layout

```text
.
├── interactionModels/custom/en-US.json
├── interactionModels/custom/pt-BR.json
├── lambda/lambda_function.py
├── lambda/requirements.txt
├── lambda/.env.example
├── skill.json
└── README.md
```

## Requirements

You need an Amazon Developer account, an AWS account with permission to create Lambda functions, and a Google AI Studio API key. The examples below use **Python 3.12** and the AWS region **US East (N. Virginia), `us-east-1`**. Keep Alexa, Lambda, and the API deployment in the same region whenever the Alexa Console offers that choice.

## Quick security setup

1. Create a key at [Google AI Studio](https://aistudio.google.com/app/apikey).
2. In AWS Lambda, open the function's **Configuration → Environment variables**.
3. Add `GOOGLE_API_KEY` with your key as the value.
4. Optionally add `GEMINI_MODEL` with `gemini-3.1-flash-lite` (the default).
5. Do not commit `.env`, copied Lambda ZIP files, or logs containing secrets. The `.gitignore` file already excludes these patterns.

For local testing only, copy `lambda/.env.example` to `lambda/.env` and set the key. The production Lambda code reads environment variables directly; `.env` is not required in AWS and is intentionally ignored by Git.

## Create the Alexa skill in the console

1. Open [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) and choose **Create Skill**.
2. Enter a skill name such as **Gemini Assistant**. Select **Custom** for the model, choose **Provision your own**, and select **Alexa-hosted** only if you want Amazon to host the code. This repository is designed for an AWS Lambda endpoint, so choose **Provision your own** if the Lambda will be in your AWS account.
3. Select a primary language. For English choose **English (US)**. To support Portuguese as well, add **Portuguese (Brazil)** from **Languages** after creation.
4. Choose **Start from Scratch**.
5. Open **Interaction Model → JSON Editor**. Select the appropriate locale and paste the matching file from `interactionModels/custom/`:
   - `en-US.json` for English;
   - `pt-BR.json` for Brazilian Portuguese.
6. Click **Save Model**, then **Build Model**. Repeat for every locale.
7. Open **Endpoint**. Select **AWS Lambda ARN** and paste the ARN of your Lambda function. If you use an AWS account in `us-east-1`, the ARN normally begins with `arn:aws:lambda:us-east-1:`.
8. In AWS Lambda, add the Alexa Skills Kit trigger and authorize the Alexa skill ID shown by the console. This prevents unrelated skills from invoking the function.
9. In the Alexa Console, use **Test** and enable testing for **Development**. Test in the locale you are editing.

The included `skill.json` is a reference manifest, not a substitute for connecting your own Lambda. Replace `REPLACE_WITH_YOUR_LAMBDA_ARN` only if you use an Alexa CLI or manifest-based workflow. Do not reuse the ARN that may have appeared in an older export.

## Create the AWS Lambda function

1. Open the [AWS Lambda console](https://console.aws.amazon.com/lambda/), select region **US East (N. Virginia) / `us-east-1`**, and choose **Create function**.
2. Choose **Author from scratch**.
3. Name it, for example, `gemini-alexa-skill`.
4. Choose **Python 3.12** as the runtime. Create or select an execution role with the basic Lambda logging policy.
5. Download the dependencies from `lambda/requirements.txt` and package them with `lambda/lambda_function.py` at the root of the ZIP. A simple Linux/macOS packaging flow is:

   ```bash
   mkdir -p build
   python3 -m pip install -r lambda/requirements.txt -t build
   cp lambda/lambda_function.py build/
   cd build && zip -r ../gemini-alexa-lambda.zip .
   ```

6. Upload `gemini-alexa-lambda.zip` under **Code → Upload from → .zip file**.
7. Set the handler to `lambda_function.lambda_handler`.
8. Under **Configuration → Environment variables**, add `GOOGLE_API_KEY`. Do not hard-code it in Python.
9. Set the Lambda timeout to at least **20 seconds**. The code's HTTP timeout is 15 seconds.
10. Add an **Alexa Skills Kit** trigger and restrict it to your skill ID.
11. Copy the Lambda ARN into the Alexa Console endpoint configuration.

If the console presents a Lambda function region choice, select **North America / US East (N. Virginia)** to match `us-east-1`. AWS may label the Alexa endpoint region as **North America** rather than spelling out the AWS region.

## Invocation and intents

### Invocation names

- English: `gemini assistant` — say **“Alexa, open Gemini Assistant.”**
- Portuguese: `assistente gemini` — say **“Alexa, abra Assistente Gemini.”**

The invocation name is configured in each locale's JSON file. It must be two or more words and should be easy to pronounce.

### Custom intent

`ChatIntent` receives the user's question in the `query` slot:

```json
{
  "name": "ChatIntent",
  "slots": [
    { "name": "query", "type": "AMAZON.SearchQuery" }
  ],
  "samples": ["ask {query}", "me diga {query}"]
}
```

Built-in intents handled by the Lambda include `AMAZON.HelpIntent`, `AMAZON.CancelIntent`, `AMAZON.StopIntent`, `AMAZON.FallbackIntent`, and `SessionEndedRequest`.

## Test phrases

English:

- “Alexa, open Gemini Assistant.”
- “Ask Gemini Assistant what causes rain.”
- “Ask Gemini Assistant to explain black holes.”

Portuguese:

- “Alexa, abra Assistente Gemini.”
- “Pergunte ao Assistente Gemini o que é fotossíntese.”
- “Pergunte ao Assistente Gemini como fazer pão.”

## Common problems

**The skill says that the service is not configured.** Check that the Lambda environment variable is named exactly `GOOGLE_API_KEY` and that you deployed the new code to the same function connected to Alexa.

**Alexa cannot reach Lambda.** Check the region, Lambda trigger, skill ID restriction, function ARN, and that the handler is `lambda_function.lambda_handler`.

**The model does not build.** Ensure the JSON editor contains only one locale's interaction model at a time and click **Save Model** before **Build Model**. Use the exact locale file from this repository.

**Gemini returns an API error.** Confirm that the key is active, the Generative Language API is available for the associated Google project, billing or quota requirements are satisfied, and the model name is supported for that API account.

## License

MIT. See `LICENSE` if you add one for your fork. You are responsible for complying with Google Gemini, Amazon Alexa, AWS, and any applicable privacy requirements.

---

# Assistente Gemini para Alexa (Português)

Uma Custom Skill reutilizável da Alexa que envia perguntas de voz para a API do Google Gemini. O projeto inclui modelos em inglês (`en-US`) e português do Brasil (`pt-BR`) e um backend Python para AWS Lambda.

> **Segurança:** este repositório não contém chave de API. Crie sua própria chave no Google AI Studio e informe-a à Lambda pela variável de ambiente `GOOGLE_API_KEY`. Nunca coloque a chave real no GitHub, no modelo de interação ou no código.

## O que foi incluído

- Experiência de voz em inglês e português do Brasil.
- `ChatIntent` com slot `AMAZON.SearchQuery`.
- Respostas curtas e adequadas para fala, sem Markdown.
- Histórico limitado à sessão atual da Alexa.
- Tratamento de timeout e erros da API.
- Nenhum ARN da conta original no pacote.

## Pré-requisitos

Você precisa de uma conta de desenvolvedor Amazon, uma conta AWS com permissão para criar Lambda e uma chave do Google AI Studio. O passo a passo usa **Python 3.12** e a região AWS **US East (N. Virginia), `us-east-1`**. Quando possível, mantenha Alexa, Lambda e o serviço de API na mesma região.

## Como colocar a chave na variável

1. Crie uma chave no [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Na AWS Lambda, abra **Configuration → Environment variables**.
3. Adicione a variável com o nome exato `GOOGLE_API_KEY` e cole a chave no valor.
4. Opcionalmente, adicione `GEMINI_MODEL` com o valor `gemini-3.1-flash-lite`.
5. Nunca faça commit de `.env`, ZIPs com a Lambda ou logs que contenham segredos. O `.gitignore` já bloqueia esses padrões.

Para testar localmente, copie `lambda/.env.example` para `lambda/.env` e preencha a chave. Em produção, a Lambda usa as variáveis de ambiente da AWS; o `.env` não é necessário e é ignorado pelo Git.

## Como criar a skill na página da Alexa

1. Abra o [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) e clique em **Create Skill**.
2. Dê um nome, por exemplo, **Assistente Gemini**. Selecione **Custom** no modelo, **Provision your own** e, se for usar a Lambda da sua conta AWS, não escolha hospedagem Alexa-hosted.
3. Escolha **English (US)** como idioma principal. Para ter português, adicione **Portuguese (Brazil)** na área **Languages**.
4. Escolha **Start from Scratch**.
5. Entre em **Interaction Model → JSON Editor** e cole o arquivo correspondente:
   - `interactionModels/custom/en-US.json` para inglês;
   - `interactionModels/custom/pt-BR.json` para português do Brasil.
6. Clique em **Save Model** e depois **Build Model**. Repita para cada idioma.
7. Abra **Endpoint**, selecione **AWS Lambda ARN** e cole o ARN da sua função. Em `us-east-1`, ele começa normalmente com `arn:aws:lambda:us-east-1:`.
8. Na AWS Lambda, adicione o trigger **Alexa Skills Kit** e restrinja-o ao Skill ID exibido no console.
9. Na aba **Test**, habilite o teste em **Development** e teste no idioma editado.

O `skill.json` incluído é um manifesto de referência. Ele não substitui a conexão da sua própria Lambda. Se usar CLI ou manifesto, substitua `REPLACE_WITH_YOUR_LAMBDA_ARN` pelo ARN da sua função. Não reutilize o ARN da exportação antiga.

## Como criar a Lambda

1. Abra o console [AWS Lambda](https://console.aws.amazon.com/lambda/) na região **US East (N. Virginia) / `us-east-1`**.
2. Escolha **Create function → Author from scratch**.
3. Use um nome como `gemini-alexa-skill`.
4. Selecione **Python 3.12** e crie uma role com a permissão básica de logs do Lambda.
5. Instale as dependências de `lambda/requirements.txt`, copie `lambda/lambda_function.py` para a raiz do ZIP e faça o upload. O handler é `lambda_function.lambda_handler`.
6. Em **Configuration → Environment variables**, coloque `GOOGLE_API_KEY`.
7. Configure timeout de pelo menos **20 segundos**.
8. Adicione o trigger **Alexa Skills Kit**, restrito ao Skill ID da sua skill.
9. Copie o ARN da Lambda para **Endpoint** no Alexa Developer Console.

Se aparecer uma opção de região da Lambda na Alexa, escolha **North America / US East (N. Virginia)** para corresponder à `us-east-1`. A Alexa pode exibir o nome comercial **North America** em vez do nome completo da região AWS.

## Comando de ativação e intents

- Inglês: `gemini assistant`; diga **“Alexa, open Gemini Assistant.”**
- Português: `assistente gemini`; diga **“Alexa, abra Assistente Gemini.”**

O nome de ativação fica no `invocationName` de cada JSON. A intent personalizada se chama `ChatIntent` e recebe a pergunta no slot `query`. As intents integradas de ajuda, parar, cancelar, fallback e encerramento de sessão já são tratadas pela Lambda.

## Frases de teste

- **“Alexa, abra Assistente Gemini.”**
- **“Pergunte ao Assistente Gemini o que é fotossíntese.”**
- **“Pergunte ao Assistente Gemini como fazer pão.”**

## Solução de problemas

Se disser que o serviço não foi configurado, confira o nome exato `GOOGLE_API_KEY` e se publicou o código na mesma Lambda ligada à Alexa. Se a Alexa não alcançar a Lambda, confira região, trigger, Skill ID, ARN e handler. Se o modelo não compilar, salve antes de construir e use um JSON por idioma. Se houver erro do Gemini, confira se a chave está ativa, se a API Generative Language está disponível no projeto Google, cotas/faturamento e se o nome do modelo é aceito.
