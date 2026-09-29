let pendingQueue = [];
let current = null;

const overlay = document.getElementById("modalOverlay");
const merchantEl = document.getElementById("modalMerchant");
const amountEl = document.getElementById("modalAmount");
const categorySelect = document.getElementById("categorySelect");
const noteInput = document.getElementById("noteInput");

async function loadEverything() {
  await loadPending();
  await loadTransactions();
  await loadTotals();
}

async function loadPending() {
  const res = await fetch("/api/pending");
  pendingQueue = await res.json();
  if (pendingQueue.length > 0 && !current) {
    showNext();
  }
}

function showNext() {
  if (pendingQueue.length === 0) {
    current = null;
    overlay.classList.add("hidden");
    return;
  }
  current = pendingQueue.shift();
  merchantEl.textContent = current.merchant;
  amountEl.textContent = `$${current.amount.toFixed(2)}`;
  noteInput.value = "";
  categorySelect.selectedIndex = 0;
  overlay.classList.remove("hidden");
}

document.getElementById("saveBtn").addEventListener("click", async () => {
  if (!current) return;
  await fetch(`/api/purchases/${current.id}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      category: categorySelect.value,
      note: noteInput.value,
    }),
  });
  await loadTransactions();
  await loadTotals();
  showNext();
});

document.getElementById("skipBtn").addEventListener("click", async () => {
  if (!current) return;
  await fetch(`/api/purchases/${current.id}/skip`, { method: "POST" });
  showNext();
});

document.getElementById("refreshBtn").addEventListener("click", async () => {
  const btn = document.getElementById("refreshBtn");
  btn.disabled = true;
  btn.textContent = "Checking...";
  const res = await fetch("/api/refresh", { method: "POST" });
  const result = await res.json();
  if (!result.ok) {
    console.warn("Refresh failed (likely IMAP not configured yet):", result.error);
  }
  await loadPending();
  await loadTransactions();
  await loadTotals();
  btn.disabled = false;
  btn.textContent = "Check for new purchases";
});

async function loadTransactions() {
  const res = await fetch("/api/transactions");
  const txs = await res.json();
  const body = document.getElementById("txBody");
  body.innerHTML = "";
  for (const tx of txs) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${tx.purchased_at ?? ""}</td>
      <td>${tx.merchant}</td>
      <td>$${tx.amount.toFixed(2)}</td>
      <td>${tx.category ?? ""}</td>
      <td>${tx.note ?? ""}</td>
    `;
    body.appendChild(row);
  }
}

async function loadTotals() {
  const res = await fetch("/api/totals");
  const totals = await res.json();
  const el = document.getElementById("totalsList");
  el.innerHTML = "";
  if (totals.length === 0) {
    el.innerHTML = `<span class="total-pill">No spending logged yet</span>`;
    return;
  }
  for (const t of totals) {
    const pill = document.createElement("span");
    pill.className = "total-pill";
    pill.textContent = `${t.category}: $${t.total.toFixed(2)} (${t.count})`;
    el.appendChild(pill);
  }
}

loadEverything();
