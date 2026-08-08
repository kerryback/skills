// The projector. Shows the join details until a question is up, then the
// question and whatever the room has said so far.

const $ = (sel) => document.querySelector(sel);

// showJoin is the instructor putting the join screen back up over a live
// question, for the student who walked in late. It is a view on this projector
// only -- voting stays open underneath and nobody's answer is disturbed.
const state = { ws: null, current: null, showJoin: false };

const CLOUD_COLOURS = [
  "#f8fafc", "#93c5fd", "#fbbf24", "#86efac", "#c4b5fd",
  "#fca5a5", "#67e8f9", "#fdba74",
];

function send(message) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify(message));
  }
}

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/display?key=${window.DISPLAY_KEY}`);
  state.ws = ws;
  ws.onmessage = (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      return;
    }
    if (message.type === "state") render(message);
  };
  ws.onclose = () => setTimeout(connect, 1500);
}

// --- rendering -------------------------------------------------------------

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function pretty(value) {
  if (value === null || value === undefined) return "—";
  const rounded = Math.round(value * 100) / 100;
  return String(rounded);
}

function render(s) {
  state.current = s;

  $("#deck-title").textContent = s.title || "No poll loaded";
  if (s.tunnel_url) {
    $("#join-url").textContent = s.tunnel_url.replace(/^https:\/\//, "");
    const qr = $("#join-qr");
    if (qr.hidden) {
      qr.src = `/api/qr.svg?key=${window.DISPLAY_KEY}`;
      qr.hidden = false;
    }
  }
  $("#join-here").textContent = s.here ? `${s.here} connected` : "";

  // What the server says is live, and what this projector is showing, are two
  // different questions once the join screen can be summoned back.
  const asking = s.loaded && s.index >= 0 && s.question;
  const showingJoin = state.showJoin || !asking;
  $("#join").hidden = !showingJoin;
  $("#asked").hidden = showingJoin;
  $("#join-live").hidden = !(state.showJoin && asking);
  if (state.showJoin && asking) {
    $("#join-live").textContent =
      `Question ${s.index + 1} is up — join now and you can still answer it`;
  }

  if (asking) {
    $("#counter").textContent = `Question ${s.index + 1} of ${s.count}`;
    $("#q-text").textContent = s.question.text;
    if (s.results) {
      $("#waiting").hidden = true;
      $("#results").hidden = false;
      drawResults(s.question, s.results, s.revealed);
    } else {
      // Results are being withheld, but the room should still see that people
      // are answering -- silence looks like a broken app.
      $("#results").hidden = true;
      $("#waiting").hidden = false;
      $("#waiting").textContent = s.responses
        ? `${s.responses} answered`
        : "Waiting for answers…";
    }
  }

  $("#status").textContent = asking ? (s.open ? "Voting open" : "Voting closed") : "";
  $("#status").className = "pill" + (s.open ? " open" : "");
  $("#tally").textContent = asking ? `${s.responses} answered · ${s.here} here` : "";

  $("#join-screen").textContent = state.showJoin ? "Back to question" : "Join screen";
  $("#join-screen").disabled = !asking;
  $("#toggle-open").textContent = s.open ? "Close voting" : "Open voting";
  $("#toggle-open").disabled = !asking;
  $("#toggle-results").textContent = s.show_results ? "Hide results" : "Show results";
  $("#toggle-results").disabled = !asking;
  $("#reveal").disabled = !s.can_reveal;
  $("#reveal").textContent = s.revealed ? "Hide answer" : "Reveal answer";
  $("#prev").disabled = !s.loaded || s.index < 0;
  $("#next").disabled = !s.loaded || s.index >= s.count - 1;
}

function drawResults(question, results, revealed) {
  const box = $("#results");
  box.innerHTML = "";
  const draw = {
    choice: drawChoice,
    wordcloud: drawCloud,
    scale: drawScale,
    number: drawNumber,
    rank: drawRank,
  }[question.type];
  if (draw) draw(box, question, results, revealed);
}

function barRow(label, fraction, value, correct) {
  const row = el("div", "bar-row" + (correct ? " correct" : ""));
  row.append(el("div", "bar-label", label));
  const track = el("div", "bar-track");
  const fill = el("div", "bar-fill");
  fill.style.width = `${Math.max(0, Math.min(1, fraction)) * 100}%`;
  track.append(fill);
  row.append(track, el("div", "bar-value", value));
  return row;
}

function drawChoice(box, question, results, revealed) {
  const bars = el("div", "bars");
  const correct = new Set(revealed ? results.answer || [] : []);
  results.options.forEach((option, index) => {
    const pct = Math.round(option.share * 100);
    bars.append(
      barRow(option.text, option.share, `${option.count} · ${pct}%`, correct.has(index))
    );
  });
  box.append(bars);
}

function drawCloud(box, question, results) {
  if (!results.words.length) {
    box.append(el("p", "waiting", "Waiting for answers…"));
    return;
  }
  const cloud = el("div", "cloud");
  results.words.forEach((entry, index) => {
    const word = el("span", null, entry.word);
    // Scale by the square root of the weight: linear scaling makes the top
    // word enormous and everything else unreadable.
    const size = 1.1 + Math.sqrt(entry.weight) * 3.6;
    word.style.fontSize = `${size}rem`;
    word.style.color = CLOUD_COLOURS[index % CLOUD_COLOURS.length];
    word.title = `${entry.count}`;
    cloud.append(word);
  });
  box.append(cloud);
}

function columns(entries) {
  const wrap = el("div", "columns");
  entries.forEach((entry) => {
    const column = el("div", "column");
    column.append(el("div", "count", entry.count ? String(entry.count) : ""));
    const stalk = el("div", "stalk");
    stalk.style.height = `${Math.max(0, Math.min(1, entry.weight)) * 100}%`;
    if (entry.highlight) stalk.style.background = "var(--good)";
    column.append(stalk, el("div", "tick", entry.tick));
    wrap.append(column);
  });
  return wrap;
}

function summary(items) {
  const wrap = el("div", "summary");
  items.forEach(([label, value, className]) => {
    const item = el("div", className || "");
    item.append(document.createTextNode(label + " "));
    item.append(el("strong", null, value));
    wrap.append(item);
  });
  return wrap;
}

function drawScale(box, question, results) {
  box.append(
    columns(results.points.map((p) => ({ count: p.count, weight: p.weight, tick: p.value })))
  );
  const ends = el("div", "ends");
  ends.append(el("span", null, results.min_label), el("span", null, results.max_label));
  box.append(ends);
  if (results.mean !== null) box.append(summary([["mean", pretty(results.mean)]]));
}

function drawNumber(box, question, results) {
  if (!results.bins.length) {
    box.append(el("p", "waiting", "Waiting for answers…"));
    return;
  }
  const actual = results.answer;
  box.append(
    columns(
      results.bins.map((bin) => ({
        count: bin.count,
        weight: bin.weight,
        tick: pretty(bin.start),
        highlight: actual !== null && actual !== undefined && actual >= bin.start && actual <= bin.end,
      }))
    )
  );
  const items = [
    ["mean", pretty(results.mean) + results.unit],
    ["median", pretty(results.median) + results.unit],
  ];
  if (actual !== null && actual !== undefined) {
    items.push(["actual", pretty(actual) + results.unit, "actual"]);
  }
  box.append(summary(items));
}

function drawRank(box, question, results) {
  const bars = el("div", "bars");
  const size = results.rows.length;
  results.rows.forEach((row) => {
    if (row.average === null) {
      bars.append(barRow(row.text, 0, "—"));
      return;
    }
    // A lower average position is better, so invert it for the bar length.
    const fraction = (size + 1 - row.average) / size;
    bars.append(barRow(row.text, fraction, `avg ${pretty(row.average)}`));
  });
  box.append(bars);
  box.append(summary([["complete rankings", String(results.complete)]]));
}

// --- controls --------------------------------------------------------------

function step(delta) {
  const s = state.current;
  if (!s || !s.loaded) return;
  // Moving on means the latecomer is in and the room is back to work.
  state.showJoin = false;
  send({ type: "goto", index: Math.max(-1, Math.min(s.index + delta, s.count - 1)) });
}

function toggleJoin() {
  state.showJoin = !state.showJoin;
  if (state.current) render(state.current);
}

$("#join-screen").addEventListener("click", toggleJoin);
$("#prev").addEventListener("click", () => step(-1));
$("#next").addEventListener("click", () => step(1));
$("#toggle-open").addEventListener("click", () =>
  send({ type: "open", on: !(state.current && state.current.open) })
);
$("#toggle-results").addEventListener("click", () =>
  send({ type: "results", on: !(state.current && state.current.show_results) })
);
$("#reveal").addEventListener("click", () =>
  send({ type: "reveal", on: !(state.current && state.current.revealed) })
);

$("#save").addEventListener("click", async () => {
  const button = $("#save");
  button.disabled = true;
  try {
    const response = await fetch(`/api/save?key=${window.DISPLAY_KEY}`, { method: "POST" });
    const body = await response.json();
    $("#status").textContent = body.path ? `Saved to ${body.path}` : body.error || "Could not save";
  } catch (err) {
    $("#status").textContent = "Could not save: " + err;
  } finally {
    button.disabled = false;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const keys = {
    ArrowRight: () => step(1),
    " ": () => step(1),
    ArrowLeft: () => step(-1),
    o: () => $("#toggle-open").click(),
    h: () => $("#toggle-results").click(),
    r: () => $("#reveal").click(),
    j: toggleJoin,
  };
  const action = keys[event.key];
  if (action) {
    event.preventDefault();
    action();
    showBar();
  }
});

// The control bar is on the projector too, so it stays out of the way until
// the instructor reaches for it.
let barTimer = null;
function showBar() {
  $("#bar").classList.add("shown");
  clearTimeout(barTimer);
  barTimer = setTimeout(() => $("#bar").classList.remove("shown"), 3500);
}
document.addEventListener("mousemove", showBar);

connect();
showBar();
