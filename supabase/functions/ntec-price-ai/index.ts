import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json; charset=utf-8" },
  });
}

function getApiKey() {
  const direct = Deno.env.get("SUPABASE_ANON_KEY");
  if (direct) return direct;
  try {
    const keys = JSON.parse(Deno.env.get("SUPABASE_PUBLISHABLE_KEYS") || "{}");
    return keys.default || Object.values(keys)[0] || "";
  } catch {
    return "";
  }
}

function extractOutputText(data: any): string {
  if (typeof data?.output_text === "string") return data.output_text;
  const chunks: string[] = [];
  for (const item of data?.output || []) {
    if (item?.type !== "message") continue;
    for (const content of item?.content || []) {
      if (content?.type === "output_text" && typeof content.text === "string") chunks.push(content.text);
    }
  }
  return chunks.join("\n");
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: "Use POST." }, 405);

  const authorization = req.headers.get("Authorization") || "";
  const token = authorization.replace(/^Bearer\s+/i, "").trim();
  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const anonKey = getApiKey();
  if (!token || !supabaseUrl || !anonKey) {
    return json({ error: "Sessão administrativa não identificada pelo servidor." }, 401);
  }

  const supabase = createClient(supabaseUrl, anonKey, {
    global: { headers: { Authorization: "Bearer " + token } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data: authData, error: authError } = await supabase.auth.getUser(token);
  if (authError || !authData.user) return json({ error: "Sessão inválida ou expirada. Entre novamente no portal." }, 401);
  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", authData.user.id)
    .maybeSingle();
  if (profileError || profile?.role !== "admin") return json({ error: "Somente o administrador da NTEC pode solicitar estimativas." }, 403);

  const openAiKey = Deno.env.get("OPENAI_API_KEY");
  if (!openAiKey) {
    return json({
      error: "A função de IA está instalada, mas falta configurar OPENAI_API_KEY nos Secrets das Edge Functions do Supabase. O estimador por índice continua disponível.",
      code: "OPENAI_API_KEY_MISSING",
    }, 503);
  }

  let body: any;
  try { body = await req.json(); } catch { return json({ error: "Corpo JSON inválido." }, 400); }
  const itemName = String(body?.item_name || "").trim().slice(0, 250);
  const category = String(body?.category || "").trim().slice(0, 180);
  const unit = String(body?.unit || "").trim().slice(0, 40);
  const itemCode = String(body?.item_code || "").trim().slice(0, 30);
  const currentPrice = Number(body?.current_price);
  const priceLabel = String(body?.price_label || "").trim().slice(0, 80);
  const notes = String(body?.notes || "").trim().slice(0, 1200);
  if (!itemName || !category || !unit || !Number.isFinite(currentPrice) || currentPrice < 0) {
    return json({ error: "Item, especialidade, unidade e preço atual são obrigatórios." }, 400);
  }

  const today = new Date().toISOString().slice(0, 10);
  const prompt = [
    "Você é analista de custos da NTEC Engenharia & Geotecnia, em São Paulo, Brasil. Data de referência: " + today + ".",
    "Pesquise na web usando fontes acessíveis e recentes para formar uma estimativa comercial de preço para este serviço de engenharia civil.",
    "Item: " + itemName,
    "Código interno: " + (itemCode || "não informado"),
    "Especialidade: " + category,
    "Unidade: " + unit,
    "Preço de referência atual da NTEC: R$ " + currentPrice.toFixed(2),
    "Rótulo textual da planilha: " + (priceLabel || "nenhum"),
    "Observações do escopo: " + (notes || "nenhuma"),
    "Contexto original: a tabela RG 28 foi criada em novembro/2022. Não trate o preço-base antigo como cotação atual.",
    "Regras:",
    "1. Use web search e procure preços publicados / tabelas públicas / composições de custos / contratos ou cotações acessíveis para o MESMO serviço e unidade no Brasil, priorizando São Paulo quando houver evidência.",
    "2. Nunca invente cotações, fontes, URLs ou fatos. Se não achar comparáveis adequados, marque confidence=low, use faixa conservadora apenas se justificável e explique que falta evidência. Não converta unidades sem explicar.",
    "3. Separe evidência de mercado de correção por inflação. Indique fatores de custo que afetam a execução: deslocamento/mobilização, equipe, equipamento, materiais, quantidade, impostos e margem, conforme o serviço.",
    "4. Recomende valor unitário, faixa inferior/superior plausível e percentual de reajuste anual sugerido para os próximos 12 meses. Percentual de reajuste NÃO é taxa oficial garantida: explique quais indicadores/pressões o justificam.",
    "5. Compare o preço atual com a faixa e marque abaixo, na_faixa, acima ou sem_preco_numerico, conforme o preço atual da NTEC versus a faixa de mercado estimada.",
    "6. Use reais (BRL), valores numéricos sem formatação na resposta JSON, e cite 1-5 fontes reais em sources (title, url, summary). Não baseie afirmação em fonte não listada.",
    "7. Este é suporte à decisão, não preço garantido, licitação oficial nem parecer técnico/contábil. A recomendação deve ser revisada pelo administrador antes de aplicada.",
    "Responda somente de acordo com o JSON Schema exigido."
  ].join("\n");

  const schema = {
    type: "object",
    additionalProperties: false,
    properties: {
      market_price_min: { type: "number" },
      market_price_max: { type: "number" },
      recommended_price: { type: "number" },
      annual_adjustment_percent: { type: "number" },
      assessment: { type: "string", enum: ["abaixo", "na_faixa", "acima", "sem_preco_numerico"] },
      confidence: { type: "string", enum: ["low", "medium", "high"] },
      rationale: { type: "string" },
      cost_factors: { type: "array", items: { type: "string" } },
      sources: {
        type: "array",
        items: {
          type: "object",
          additionalProperties: false,
          properties: {
            title: { type: "string" },
            url: { type: "string" },
            summary: { type: "string" },
          },
          required: ["title", "url", "summary"],
        },
      },
    },
    required: ["market_price_min", "market_price_max", "recommended_price", "annual_adjustment_percent", "assessment", "confidence", "rationale", "cost_factors", "sources"],
  };

  let response: Response;
  try {
    response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: { "Authorization": "Bearer " + openAiKey, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: Deno.env.get("NTEC_PRICE_AI_MODEL") || "gpt-5.5",
        tools: [{ type: "web_search", search_context_size: "low" }],
        tool_choice: "required",
        input: prompt,
        text: { format: { type: "json_schema", name: "ntec_price_estimate", strict: true, schema } },
        max_output_tokens: 2400,
      }),
      signal: AbortSignal.timeout(65000),
    });
  } catch (error) {
    return json({ error: "Não foi possível consultar o serviço de IA agora.", detail: String(error).slice(0, 300) }, 502);
  }
  const raw = await response.text();
  if (!response.ok) {
    let details = raw.slice(0, 700);
    try {
      const err = JSON.parse(raw)?.error;
      details = String(err?.message || details).slice(0, 700);
    } catch {}
    return json({ error: "A API de IA recusou a solicitação.", detail: details, status: response.status }, response.status === 429 ? 429 : 502);
  }

  let data: any;
  try { data = JSON.parse(raw); } catch { return json({ error: "A resposta da API não veio em JSON válido." }, 502); }
  let estimate: any;
  try { estimate = JSON.parse(extractOutputText(data)); } catch {
    return json({ error: "Não consegui interpretar a estimativa retornada pela IA.", output: extractOutputText(data).slice(0, 1000) }, 502);
  }

  const min = Number(estimate.market_price_min);
  const max = Number(estimate.market_price_max);
  const recommended = Number(estimate.recommended_price);
  const annual = Number(estimate.annual_adjustment_percent);
  if (![min, max, recommended, annual].every(Number.isFinite) || min < 0 || max < min || recommended < 0 || annual < -20 || annual > 100) {
    return json({ error: "A IA devolveu uma faixa ou percentual fora dos limites de validação. Gere uma nova análise." }, 502);
  }
  if (estimate.assessment !== "sem_preco_numerico" && currentPrice < min) estimate.assessment = "abaixo";
  else if (estimate.assessment !== "sem_preco_numerico" && currentPrice > max) estimate.assessment = "acima";
  else if (estimate.assessment !== "sem_preco_numerico") estimate.assessment = "na_faixa";

  const annotations: any[] = [];
  for (const item of data?.output || []) {
    if (item?.type !== "message") continue;
    for (const content of item?.content || []) {
      for (const a of content?.annotations || []) {
        if (a?.type === "url_citation" && a.url) annotations.push({ title: a.title || a.url, url: a.url, summary: "" });
      }
    }
  }
  const normalizeSourceUrl = (value: string) => {
    try {
      const u = new URL(value);
      u.hash = "";
      u.search = "";
      return (u.origin + u.pathname).replace(/\/$/, "").toLowerCase();
    } catch {
      return "";
    }
  };
  // Only return sources actually cited in the Responses API web-search annotations.
  // Model-suggested links that cannot be matched to a tool citation are discarded.
  const citedByUrl = new Map<string, any>();
  for (const source of annotations) {
    const url = String(source.url || "").trim();
    const key = normalizeSourceUrl(url);
    if (/^https?:\/\//i.test(url) && key && !citedByUrl.has(key)) {
      citedByUrl.set(key, {
        title: String(source.title || url).slice(0, 220),
        url,
        summary: "",
      });
    }
  }
  const sourceMap = new Map<string, any>();
  for (const suggestion of estimate.sources || []) {
    const url = String(suggestion.url || "").trim();
    const key = normalizeSourceUrl(url);
    const citation = citedByUrl.get(key);
    if (citation && !sourceMap.has(key)) {
      sourceMap.set(key, {
        ...citation,
        title: String(suggestion.title || citation.title).slice(0, 220),
        summary: String(suggestion.summary || "").slice(0, 500),
      });
    }
  }
  for (const [key, citation] of citedByUrl.entries()) {
    if (!sourceMap.has(key)) sourceMap.set(key, citation);
  }
  const sources = [...sourceMap.values()].slice(0, 8);
  return json({
    estimate: {
      market_price_min: Math.round(min * 100) / 100,
      market_price_max: Math.round(max * 100) / 100,
      recommended_price: Math.round(recommended * 100) / 100,
      annual_adjustment_percent: annual,
      assessment: estimate.assessment,
      confidence: estimate.confidence,
      rationale: String(estimate.rationale || "").slice(0, 3000),
      cost_factors: Array.isArray(estimate.cost_factors) ? estimate.cost_factors.map((x: any) => String(x).slice(0, 400)).slice(0, 12) : [],
      sources,
      model: Deno.env.get("NTEC_PRICE_AI_MODEL") || "gpt-5.5",
      data_as_of: today,
    },
  });
});
