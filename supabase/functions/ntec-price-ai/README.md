# NTEC — Assistente de preço por IA

A função `ntec-price-ai` faz pesquisa de mercado sob demanda usando a API Responses da OpenAI com a ferramenta de pesquisa na web. A chave é usada somente no servidor (Supabase Edge Function) e não deve ser colocada no código do portal ou no GitHub.

## Ativar pesquisa real

1. Abra o projeto Supabase da NTEC.
2. Vá em **Project Settings → Edge Functions → Secrets** (a localização do menu pode variar na interface).
3. Adicione o secret:
   - Nome: `OPENAI_API_KEY`
   - Valor: sua chave da API OpenAI.
4. Opcionalmente adicione `NTEC_PRICE_AI_MODEL` com o nome de um modelo disponível para sua conta. O padrão deste projeto é `gpt-5.5`.
5. Abra o portal como administrador, entre em **Valores de Referência para Proposta**, selecione um item e clique em **Pesquisar mercado com IA**.

A função exige autenticação válida do Supabase e perfil `admin`; a configuração de JWT permanece habilitada. Não envie a chave por chat, não a inclua em arquivos do frontend e não a comite no repositório.

## Uso e custo

A pesquisa real só acontece quando o administrador clica no botão. As chamadas à API da OpenAI podem ser cobradas conforme a conta, modelo e ferramenta de pesquisa. A função informa erro quando a chave falta ou a API não está disponível. A estimativa por índice continua disponível sem a chave.

## Limites da estimativa

A recomendação é uma referência para revisão humana, não uma cotação garantida nem um preço oficial. Compare a unidade e o escopo, data e região das fontes, mobilização, deslocamento, equipe, equipamentos, impostos, overhead e margem. As fontes expostas no resultado são limitadas aos links citados pela ferramenta de pesquisa.
