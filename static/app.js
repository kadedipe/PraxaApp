const resultPanel = document.querySelector("#result");
const requestStatus = document.querySelector("#request-status");
const mcpStatus = document.querySelector("#mcp-status");
const questionInput = document.querySelector("#question");

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = String(value ?? "");
  return node.innerHTML;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function sourceCards(sources) {
  if (!sources?.length) return "<p class=\"no-sources\">No matching evidence was found.</p>";
  return sources.map((source) => `
    <details class="source-card">
      <summary><span>[${escapeHtml(source.citation)}]</span> ${escapeHtml(source.name)} <b>page ${escapeHtml(source.page)}</b></summary>
      <p>${escapeHtml(source.excerpt)}</p>
    </details>`).join("");
}

function showAnswer(question, data, invokedBy = "Human") {
  resultPanel.innerHTML = `
    <div class="result-head"><span>${escapeHtml(invokedBy)} request</span><span>${escapeHtml(data.latency_ms)} ms</span></div>
    <p class="asked">${escapeHtml(question)}</p>
    <div class="answer">${escapeHtml(data.answer).replace(/\n/g, "<br>")}</div>
    <h3>Verified sources <span>${data.sources.length}</span></h3>
    <div class="sources">${sourceCards(data.sources)}</div>`;
}

function showSearch(query, data, invokedBy = "WebMCP agent") {
  resultPanel.innerHTML = `
    <div class="result-head"><span>${escapeHtml(invokedBy)} search</span><span>${data.sources.length} results</span></div>
    <p class="asked">Archive search: ${escapeHtml(query)}</p>
    <h3>Matching passages</h3>
    <div class="sources">${sourceCards(data.sources)}</div>`;
}

function showError(error) {
  resultPanel.innerHTML = `<div class="error"><h2>Research interrupted</h2><p>${escapeHtml(error.message)}</p><button type="button" onclick="location.reload()">Try again</button></div>`;
}

async function askTheatre(question, invokedBy = "Human", signal) {
  requestStatus.textContent = `${invokedBy} is researching…`;
  const data = await requestJson("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
  showAnswer(question, data, invokedBy);
  requestStatus.textContent = "Research complete";
  return data;
}

document.querySelector("#ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await askTheatre(questionInput.value.trim()); } catch (error) { showError(error); requestStatus.textContent = "Request failed"; }
});

document.querySelectorAll("[data-question]").forEach((button) => button.addEventListener("click", () => {
  questionInput.value = button.dataset.question;
  questionInput.focus();
}));

async function registerWebMcpTools() {
  if (!document.modelContext?.registerTool) {
    mcpStatus.textContent = "WebMCP requires ChatGPT browser or Chrome 149+";
    mcpStatus.classList.add("unavailable");
    return;
  }

  const tools = [
    {
      name: "ask_theatre",
      description: "Answer a factual question about Broadway or West End theatre using Praxa's indexed PDFs. Returns a concise grounded answer with page-level citations and updates the visible Praxa workspace.",
      inputSchema: {
        type: "object",
        properties: { question: { type: "string", minLength: 1, maxLength: 2000, description: "A specific theatre question." } },
        required: ["question"], additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute: async ({ question }, client = {}) => {
        const data = await askTheatre(question, "WebMCP agent", client.signal);
        return JSON.stringify({ answer: data.answer, sources: data.sources });
      },
    },
    {
      name: "search_theatre_archive",
      description: "Semantically search Praxa's Broadway and West End source archive. Use this to inspect the strongest matching passages before answering or to find page-level primary evidence. Updates the visible Praxa workspace.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", minLength: 1, maxLength: 2000, description: "The topic, production, person, or fact to search for." },
          limit: { type: "integer", minimum: 1, maximum: 10, default: 5 },
        },
        required: ["query"], additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute: async ({ query, limit = 5 }, client = {}) => {
        requestStatus.textContent = "WebMCP agent is searching…";
        const data = await requestJson(`/api/search?q=${encodeURIComponent(query)}&limit=${limit}`, { signal: client.signal });
        showSearch(query, data);
        requestStatus.textContent = "Archive search complete";
        return JSON.stringify(data);
      },
    },
    {
      name: "compare_productions",
      description: "Compare two theatre productions using grounded evidence from Praxa's archive. Use when a person wants similarities, differences, longevity, venues, dates, or another explicit comparison focus. Returns citations and updates the visible workspace.",
      inputSchema: {
        type: "object",
        properties: {
          productionA: { type: "string", minLength: 1, maxLength: 200 },
          productionB: { type: "string", minLength: 1, maxLength: 200 },
          focus: { type: "string", minLength: 1, maxLength: 300, description: "What to compare, such as run length, venue, or opening date." },
        },
        required: ["productionA", "productionB", "focus"], additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute: async ({ productionA, productionB, focus }, client = {}) => {
        const question = `Compare ${productionA} and ${productionB}, focusing on ${focus}. Only state claims supported by the theatre sources.`;
        const data = await askTheatre(question, "WebMCP agent", client.signal);
        return JSON.stringify({ comparison: data.answer, sources: data.sources });
      },
    },
  ];

  for (const tool of tools) await document.modelContext.registerTool(tool);
  mcpStatus.textContent = `${tools.length} WebMCP tools active`;
  mcpStatus.classList.add("available");
}

registerWebMcpTools().catch((error) => {
  mcpStatus.textContent = "WebMCP registration failed";
  mcpStatus.classList.add("unavailable");
  console.error(error);
});
