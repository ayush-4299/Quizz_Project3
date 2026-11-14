(() => {
  const root = document.getElementById("game");
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
  const urls = { questions: root.dataset.questionsUrl, check: root.dataset.checkUrl,
                 submit: root.dataset.submitUrl, login: root.dataset.loginUrl };
  const $ = (id) => document.getElementById(id);
  const el = {
    count: $("g-count"), bar: $("g-bar"), streak: $("g-streak"), timer: $("g-timer"),
    meta: $("q-meta"), text: $("q-text"), code: $("q-code"), opts: $("opts"),
    fb: $("feedback"), fbTitle: $("fb-title"), fbText: $("fb-text"),
    prev: $("btn-prev"), next: $("btn-next"), map: $("q-map"),
    dialog: $("finish-dialog"), dialogMsg: $("finish-msg"),
    status: $("g-status"), statusText: $("g-status-text"), retry: $("g-retry"),
  };
  const state = { questions: [], seconds: 30, idx: 0, results: {}, streak: 0,
                  started: Date.now(), tick: null, deadline: 0, busy: false };

  // Renders `code` spans safely (no innerHTML, so quiz text can't inject markup).
  function rich(node, text) {
    node.textContent = "";
    String(text).split("`").forEach((part, i) => {
      if (i % 2) { const c = document.createElement("code"); c.textContent = part; node.appendChild(c); }
      else node.appendChild(document.createTextNode(part));
    });
  }

  async function api(url, body) {
    const res = await fetch(url, body ? {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify(body),
    } : {});
    if (res.status === 401) { location.href = urls.login + "?next=" + encodeURIComponent(location.pathname); return null; }
    if (!res.ok) throw new Error("Request failed");
    return res.json();
  }

  // ----- timer -----
  function stopTimer() { clearInterval(state.tick); state.tick = null; }
  function startTimer() {
    stopTimer();
    const total = state.seconds * 1000;
    state.deadline = Date.now() + total;
    state.tick = setInterval(() => {
      const left = state.deadline - Date.now();
      const frac = Math.max(0, left / total);
      el.timer.style.transform = `scaleX(${frac})`;
      el.timer.classList.toggle("low", frac < 0.25);
      if (left <= 0) { stopTimer(); answer(null); }
    }, 100);
  }

  // ----- rendering -----
  function render() {
    const q = state.questions[state.idx];
    el.count.textContent = `${state.idx + 1} / ${state.questions.length}`;
    el.meta.textContent = `Question ${state.idx + 1}`;
    rich(el.text, q.text);
    if (q.code) { el.code.hidden = false; el.code.firstElementChild.textContent = q.code; }
    else el.code.hidden = true;

    el.opts.textContent = "";
    q.options.forEach((o, i) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "opt"; b.dataset.id = o.id;
      const key = document.createElement("span"); key.className = "opt-key"; key.textContent = "ABCD"[i];
      const label = document.createElement("span"); label.className = "opt-text"; rich(label, o.text);
      const mark = document.createElement("span"); mark.className = "opt-mark"; mark.setAttribute("aria-hidden", "true");
      b.append(key, label, mark);
      b.addEventListener("click", () => answer(o.id));
      el.opts.appendChild(b);
    });

    const done = state.results[q.id];
    if (done) { showResult(q, done); }
    else { el.fb.hidden = true; el.timer.style.transform = "scaleX(1)"; el.timer.classList.remove("low"); startTimer(); }
    updateChrome();
  }

  function showResult(q, res) {
    el.opts.querySelectorAll(".opt").forEach((b) => {
      const id = Number(b.dataset.id);
      b.disabled = true;
      const mark = b.querySelector(".opt-mark");
      if (id === res.correctId) { b.classList.add("correct"); mark.textContent = "✓"; }
      else if (id === res.chosen) { b.classList.add("wrong"); mark.textContent = "✗"; }
      else b.classList.add("dim");
    });
    el.fb.hidden = false;
    el.fb.className = "feedback" + (res.timedOut ? " is-late" : res.correct ? "" : " is-wrong");
    el.fbTitle.textContent = res.timedOut ? "Time's up" : res.correct ? "Correct!" : "Not quite";
    rich(el.fbText, res.explanation || "");
    el.timer.classList.remove("low");
  }

  function showError(message) {
    el.fb.hidden = false; el.fb.className = "feedback is-late";
    el.fbTitle.textContent = "Something went wrong";
    el.fbText.textContent = message;
  }

  function updateChrome() {
    const q = state.questions[state.idx];
    const answered = Object.keys(state.results).length;
    const last = state.idx === state.questions.length - 1;
    el.bar.style.width = `${(answered / state.questions.length) * 100}%`;
    el.streak.textContent = `Streak ${state.streak}`;
    el.prev.disabled = state.idx === 0;
    el.next.textContent = last ? "Finish" : state.results[q.id] ? "Next" : "Skip";
    [...el.map.children].forEach((b, i) => {
      const r = state.results[state.questions[i].id];
      b.className = (r ? (r.correct ? "ok" : "no") : "") + (i === state.idx ? " cur" : "");
      b.setAttribute("aria-current", i === state.idx ? "step" : "false");
    });
  }

  // ----- actions -----
  async function answer(optionId) {
    const q = state.questions[state.idx];
    if (state.busy || state.results[q.id]) return;
    state.busy = true; stopTimer();
    try {
      const r = await api(urls.check, { question_id: q.id, option_id: optionId });
      if (!r) return;
      state.results[q.id] = { chosen: optionId, correctId: r.correct_option_id, correct: r.correct,
                              explanation: r.explanation, timedOut: optionId === null };
      state.streak = r.correct ? state.streak + 1 : 0;
      showResult(q, state.results[q.id]);
    } catch (e) {
      showError("Could not check that answer. Check your connection and try again.");
      if (optionId !== null) startTimer();
    } finally { state.busy = false; updateChrome(); }
  }

  function go(i) {
    if (state.busy || i < 0 || i >= state.questions.length) return;
    stopTimer(); state.idx = i; render();
  }

  function finish() {
    const left = state.questions.filter((q) => !state.results[q.id]).length;
    if (!left) return submit();
    el.dialogMsg.textContent = `${left} question${left > 1 ? "s are" : " is"} unanswered and will count as incorrect.`;
    el.dialog.returnValue = ""; el.dialog.showModal();
  }

  async function submit() {
    stopTimer();
    el.status.hidden = false; el.retry.hidden = true; el.statusText.textContent = "Scoring your answers...";
    const answers = {};
    state.questions.forEach((q) => { const r = state.results[q.id]; answers[q.id] = r ? r.chosen : null; });
    try {
      const r = await api(urls.submit, { answers, time_taken: Math.round((Date.now() - state.started) / 1000) });
      if (r) location.href = r.url;
    } catch (e) {
      el.statusText.textContent = "Your answers could not be saved. Check your connection and try again.";
      el.retry.hidden = false;
    }
  }

  el.dialog.addEventListener("close", () => { if (el.dialog.returnValue === "submit") submit(); });
  el.retry.addEventListener("click", submit);
  el.prev.addEventListener("click", () => go(state.idx - 1));
  el.next.addEventListener("click", () => (state.idx === state.questions.length - 1 ? finish() : go(state.idx + 1)));

  document.addEventListener("keydown", (e) => {
    if (el.dialog.open || e.metaKey || e.ctrlKey || e.altKey) return;
    const q = state.questions[state.idx]; if (!q) return;
    const pick = "abcd1234".indexOf(e.key.toLowerCase()) % 4;
    if (e.key.length === 1 && "abcd1234".includes(e.key.toLowerCase())) {
      const b = el.opts.children[pick]; if (b && !b.disabled) { e.preventDefault(); b.click(); }
    } else if ((e.key === "Enter" || e.key === "ArrowRight") && state.results[q.id]) { e.preventDefault(); el.next.click(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); el.prev.click(); }
  });

  // ----- boot -----
  (async () => {
    try {
      const data = await api(urls.questions);
      if (!data) return;
      state.questions = data.questions; state.seconds = data.seconds;
      state.questions.forEach((q, i) => {
        const b = document.createElement("button");
        b.type = "button"; b.textContent = i + 1; b.setAttribute("aria-label", `Go to question ${i + 1}`);
        b.addEventListener("click", () => go(i));
        el.map.appendChild(b);
      });
      state.started = Date.now();
      render();
    } catch (e) {
      el.text.textContent = "Could not load this quiz. Reload the page to try again.";
    }
  })();
})();
