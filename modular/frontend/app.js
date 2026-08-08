const modeNames = {
  "1": "Portal A2A",
  "2": "Pro-code on Foundry",
  "3a": "Hybrid code router",
  "3b": "Hybrid Foundry router",
};

const scenarioInfo = {
  "1":  { router: "Foundry",   billing: "Foundry", tech: "Foundry",  proves: "Foundry ↔ Foundry A2A (low-code)" },
  "2":  { router: "Your code", billing: "Foundry", tech: "Foundry",  proves: "Code routes; Foundry owns specialists" },
  "3a": { router: "Your code", billing: "Foundry", tech: "In-code",  proves: "One router, specialists in two worlds" },
  "3b": { router: "Foundry",   billing: "Foundry", tech: "Code A2A", proves: "Foundry calls your code via A2A" },
};

let scenario = "1";
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const send = document.querySelector("#send");
const messages = document.querySelector("#messages");
const trace = document.querySelector("#trace");
const agentLabel = document.querySelector("#agent-label");
const liveArch = document.querySelector("#live-arch");

function renderArch() {
  const info = scenarioInfo[scenario];
  liveArch.replaceChildren();
  for (const [label, value] of [["Router", info.router], ["Billing", info.billing], ["Tech", info.tech]]) {
    const chip = document.createElement("span");
    chip.className = "arch-chip";
    chip.dataset.loc = value.toLowerCase().includes("code") ? "code" : "foundry";
    const tag = document.createElement("b");
    tag.textContent = label;
    chip.append(tag, document.createTextNode(value));
    liveArch.append(chip);
  }
  const proves = document.createElement("span");
  proves.className = "arch-proves";
  proves.textContent = info.proves;
  liveArch.append(proves);
}

window.addEventListener("DOMContentLoaded", () => {
  window.lucide?.createIcons();
  renderArch();
});

document.querySelectorAll(".scenario").forEach((button) => {
  button.addEventListener("click", () => {
    scenario = button.dataset.scenario;
    document.querySelectorAll(".scenario").forEach((item) => {
      const selected = item === button;
      item.classList.toggle("active", selected);
      item.setAttribute("aria-checked", String(selected));
    });
    document.querySelector("#mode-title").textContent = modeNames[scenario];
    renderArch();
  });
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || send.disabled) return;

  if (messages.querySelector(".empty-state")) messages.replaceChildren();
  appendMessage("user", "You", message);
  input.value = "";
  input.style.height = "auto";
  send.disabled = true;
  agentLabel.textContent = "Routing request...";

  try {
    const result = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, message }),
    });
    const body = await result.json();
    if (!result.ok) throw new Error(body.detail || "The request failed.");
    appendMessage("agent", body.agent, body.reply);
    renderTrace(body.trace);
    agentLabel.textContent = `Answered by ${body.agent}`;
  } catch (error) {
    appendMessage("error", "Connection error", error.message);
    agentLabel.textContent = "Request failed";
  } finally {
    send.disabled = false;
    input.focus();
  }
});

function appendMessage(kind, label, text) {
  const item = document.createElement("article");
  item.className = `message ${kind}`;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = label;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  item.append(meta, bubble);
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function renderTrace(steps) {
  trace.replaceChildren();
  steps.forEach(({ step, detail }) => {
    const item = document.createElement("li");
    const heading = document.createElement("strong");
    heading.textContent = step;
    item.append(heading, document.createTextNode(detail));
    trace.append(item);
  });
}