const state = {
  cabinet: {},
  mux: {},
  fleet: {},
  scheduler: {},
  sessions: [],
};

const formMappings = {
  cabinet: document.getElementById("cabinet-form"),
  mux: document.getElementById("mux-form"),
  fleet: document.getElementById("fleet-form"),
  scheduler: document.getElementById("scheduler-form"),
};

async function fetchState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  Object.assign(state, data);
  hydrateForms();
  renderMuxOutputs();
  renderSessions();
  await fetchDataLake();
}

function hydrateForms() {
  for (const [key, form] of Object.entries(formMappings)) {
    if (!form || !state[key]) continue;
    Array.from(form.elements).forEach((input) => {
      if (input.name && state[key][input.name] !== undefined) {
        input.value = state[key][input.name];
      }
    });
  }
}

function renderMuxOutputs() {
  const container = document.getElementById("mux-outputs");
  container.innerHTML = "";
  const outputs = state.mux.outputs_enabled || [];
  outputs.forEach((enabled, index) => {
    const wrapper = document.createElement("label");
    wrapper.className = "toggle";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = enabled;
    checkbox.addEventListener("change", () => {
      state.mux.outputs_enabled[index] = checkbox.checked;
    });
    wrapper.appendChild(checkbox);
    wrapper.append(`Output ${index + 1}`);
    container.appendChild(wrapper);
  });
}

function renderSessions() {
  const table = document.getElementById("session-table");
  table.innerHTML = "";
  const header = document.createElement("div");
  header.className = "table-row header";
  header.innerHTML =
    "<div>EV</div><div>SOC %</div><div>Status</div><div>Wait (s)</div><div>Urgency</div><div>Power kW</div>";
  table.appendChild(header);

  state.sessions.forEach((session) => {
    const row = document.createElement("div");
    row.className = "table-row";
    row.innerHTML = `
      <div>${session.ev_id}</div>
      <div>${session.soc_percent.toFixed(1)}</div>
      <div>${session.status}</div>
      <div>${session.wait_seconds.toFixed(0)}</div>
      <div>${session.urgency_level}</div>
      <div>${session.allocated_power_kw.toFixed(1)}</div>
    `;
    table.appendChild(row);
  });
}

async function fetchDataLake() {
  const filter = document.getElementById("datalake-filter").value;
  const url = filter ? `/api/datalake?ev_id=${filter}` : "/api/datalake";
  const response = await fetch(url);
  const data = await response.json();
  const table = document.getElementById("datalake-table");
  table.innerHTML = "";
  const header = document.createElement("div");
  header.className = "table-row header";
  header.innerHTML =
    "<div>Time</div><div>EV</div><div>Event</div><div>Power kW</div><div>SOC %</div><div>MUX Port</div>";
  table.appendChild(header);

  data.entries.slice(-10).reverse().forEach((entry) => {
    const row = document.createElement("div");
    row.className = "table-row";
    row.innerHTML = `
      <div>${new Date(entry.timestamp).toLocaleTimeString()}</div>
      <div>${entry.ev_id}</div>
      <div>${entry.event}</div>
      <div>${entry.allocated_power_kw.toFixed(1)}</div>
      <div>${entry.soc_percent.toFixed(1)}</div>
      <div>${entry.mux_port ?? "-"}</div>
    `;
    table.appendChild(row);
  });

  const downloadLink = document.getElementById("datalake-download");
  downloadLink.href = filter ? `/api/datalake/download?ev_id=${filter}` : "/api/datalake/download";
}

function collectFormData() {
  const payload = {};
  for (const [key, form] of Object.entries(formMappings)) {
    payload[key] = {};
    Array.from(form.elements).forEach((input) => {
      if (input.name) {
        payload[key][input.name] = Number(input.value);
      }
    });
  }
  payload.mux.outputs_enabled = state.mux.outputs_enabled;
  return payload;
}

async function updateConfig() {
  const payload = collectFormData();
  await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await fetchState();
}

async function runScheduler() {
  await fetch("/api/schedule", { method: "POST" });
  await fetchState();
}

Object.values(formMappings).forEach((form) => {
  form.addEventListener("change", () => {
    updateConfig();
  });
});

document.getElementById("schedule-btn").addEventListener("click", () => {
  runScheduler();
});

document.getElementById("datalake-refresh").addEventListener("click", () => {
  fetchDataLake();
});

document.getElementById("datalake-filter").addEventListener("change", () => {
  fetchDataLake();
});

fetchState();
