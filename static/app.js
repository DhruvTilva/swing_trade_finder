document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("start-btn");
  const analyzeAllBtn = document.getElementById("analyzeAllBtn");
  const loader = document.getElementById("loader");
  const statusEl = document.getElementById("status");
  const table = document.getElementById("result-table");
  const tbody = document.getElementById("results");

  //  FINDING (BEST + WORST)
  startBtn.addEventListener("click", async () => {
    statusEl.textContent = "Running analysis...";
    table.classList.add("hidden");
    tbody.innerHTML = "";
    loader.classList.remove("hidden");

    try {
      const resp = await fetch("/analyze", { method: "POST" });
      if (!resp.ok) throw new Error("Server error");

      const data = await resp.json();
      console.log(data);

      const rows = [];
      if (data.top_positive) rows.push(data.top_positive);
      if (data.top_negative) rows.push(data.top_negative);

      if (rows.length === 0) {
        statusEl.textContent = "No results returned.";
        return;
      }

      renderRows(rows, true);
      statusEl.textContent = "Analysis completed";

    } catch (e) {
      console.error(e);
      statusEl.textContent = "Error: " + e.message;
    } finally {
      loader.classList.add("hidden");
    }
  });

  // ANALYZE ALL 
  analyzeAllBtn.addEventListener("click", async () => {
    statusEl.textContent = "Analyzing all CSV stocks...";
    table.classList.add("hidden");
    tbody.innerHTML = "";
    loader.classList.remove("hidden");

    try {
      const resp = await fetch("/analyze-all", { method: "POST" });
      if (!resp.ok) throw new Error("Server error");

      const json = await resp.json();
      console.log(json);

      if (json.status !== "ok" || !json.data || json.data.length === 0) {
        statusEl.textContent = "No valid results found.";
        return;
      }

      renderRows(json.data, false);
      statusEl.textContent = `Analysis completed (${json.data.length} stocks)`;

    } catch (e) {
      console.error(e);
      statusEl.textContent = "Error: " + e.message;
    } finally {
      loader.classList.add("hidden");
    }
  });

  // TABLE RENDERER
  function renderRows(rows, highlightBestWorst) {
    tbody.innerHTML = "";

    rows.forEach((s, idx) => {
      const tr = document.createElement("tr");

      if (highlightBestWorst) {
        if (idx === 0) tr.style.backgroundColor = "#e8f8ee"; // positive
        if (idx === 1) tr.style.backgroundColor = "#fdecea"; // negative
      }

      tr.innerHTML = `
        <td>${s.symbol}</td>
        <td>${s.last_price}</td>
        <td>${s.upside_15d}%</td>
        <td>${s.upside_30d}%</td>
        <td>${s.upside_60d}%</td>
        <td>${s.upside_90d}%</td>
        <td>${s.target_90d ?? "-"}</td>
        <td>${s.stop_loss ?? "-"}</td>
        <td>${s.sentiment}</td>
        <td>${s.rationale ?? "-"}</td>
      `;

      tbody.appendChild(tr);
    });

    table.classList.remove("hidden");
  }
});
