document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("start-btn");
  const loader = document.getElementById("loader");
  const statusEl = document.getElementById("status");
  const table = document.getElementById("result-table");
  const tbody = document.getElementById("results");

  startBtn.addEventListener("click", async () => {
    statusEl.textContent = "Running analysis...";
    table.classList.add("hidden");
    tbody.innerHTML = "";
    loader.classList.remove("hidden");

    try {
      const resp = await fetch("/analyze", { method: "POST" });
      if (!resp.ok) {
        throw new Error("Server error: " + resp.status);
      }

      const data = await resp.json();
      console.log(data);

      const rows = [];
      if (data.top_positive) rows.push(data.top_positive);
      if (data.top_negative) rows.push(data.top_negative);

      if (rows.length === 0) {
        statusEl.textContent = "No results returned.";
        return;
      }

      rows.forEach((s, idx) => {
        const tr = document.createElement("tr");

        // Optional row coloring
        if (idx === 0) tr.style.backgroundColor = "#e8f8ee"; // positive
        if (idx === 1) tr.style.backgroundColor = "#fdecea"; // negative

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
      statusEl.textContent = "Analysis completed";

    } catch (e) {
      console.error(e);
      statusEl.textContent = "Error: " + e.message;
    } finally {
      loader.classList.add("hidden");
    }
  });
});
