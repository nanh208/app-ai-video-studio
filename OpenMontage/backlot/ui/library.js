import { el, fmtAgo, getJSON, subscribe, thumbURL, mediaURL } from "/ui/lib.js";

const grid = document.getElementById("grid");
const modal = document.getElementById("modal");
const THEME_KEY = "backlot.theme";
let currentTheme = localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";
let metaInfo = null;

function applyTheme(theme) {
  currentTheme = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = currentTheme;
  localStorage.setItem(THEME_KEY, currentTheme);
}

function renderThemeToggle() {
  const next = currentTheme === "light" ? "dark" : "light";
  return el("button", {
    class: "theme-toggle",
    type: "button",
    title: `Switch to ${next} theme`,
    "aria-label": `Switch to ${next} theme`,
    "aria-pressed": currentTheme === "light" ? "true" : "false",
    onclick: () => {
      applyTheme(next);
      const replacement = renderThemeToggle();
      document.querySelector(".theme-toggle").replaceWith(replacement);
    },
  }, el("span", { class: "theme-toggle-icon", "aria-hidden": "true" }, currentTheme === "light" ? "☾" : "☀"));
}

applyTheme(currentTheme);
document.getElementById("liveBadge").before(renderThemeToggle());

function closeModal() {
  modal.classList.remove("open");
  modal.innerHTML = "";
}

function openModal(content) {
  modal.innerHTML = "";
  const page = el("div", { class: "modal-page" }, content);
  const closeBtn = el("button", { class: "modal-close", onclick: closeModal }, "✕ CLOSE");
  modal.append(closeBtn, page);
  modal.classList.add("open");
}

function playVideo(projectId, videoPath, title) {
  const videoSrc = mediaURL(projectId, videoPath);
  const content = el("div", { class: "video-modal-wrap" },
    el("div", { class: "video-modal-header" },
      el("span", { style: "color:var(--amber);font-weight:600" }, `▶ ${title || "Video Render"}`),
      el("span", { style: "color:var(--text-3)" }, videoPath),
    ),
    el("video", { src: videoSrc, controls: "true", autoplay: "true" })
  );
  openModal(content);
}

function miniRail(states) {
  const rail = el("div", { class: "mini-rail" });
  for (const s of states) {
    const cls = s.status === "completed" ? "d"
      : s.status === "in_progress" ? "a"
      : s.status === "awaiting_human" ? "w" : "";
    rail.append(el("i", { class: cls, title: `${s.name}: ${s.status}` }));
  }
  return rail;
}

function card(p) {
  const poster = el("div", { class: "lib-poster" });
  if (p.poster) {
    poster.append(el("img", { src: thumbURL(p.project_id, p.poster, 640), loading: "lazy", alt: "" }));
  } else {
    poster.append(el("span", { class: "lp-txt" }, "NO MEDIA YET"));
  }
  if (p.live && p.active_stage) {
    poster.append(el("span", { class: "lp-live" },
      el("span", { class: "dot" }),
      p.awaiting_human ? "◈ AWAITING YOU" : `LIVE · ${p.active_stage.toUpperCase()}`));
  } else if (p.awaiting_human) {
    poster.append(el("span", { class: "lp-live" }, "◈ AWAITING YOU"));
  }

  const meta = el("div", { class: "lb-meta" },
    el("span", { class: "chip" }, p.pipeline_type || "unknown"),
    p.scene_count ? el("span", { class: "chip" }, `${p.scene_count} scenes`) : null,
    p.render_count ? el("span", { class: "chip", style: "border-color:var(--green);color:var(--green)" }, `▶ ${p.render_count} renders`) : null,
    el("span", { class: "when" }, fmtAgo(p.last_activity)),
  );

  const staticSuffix = new URLSearchParams(location.search).has("static") ? "?static=1" : "";
  
  const cardEl = el("div", { class: `lib-card${p.live ? " live-card" : ""}` },
    el("a", { href: `/p/${p.project_id}${staticSuffix}`, style: "text-decoration:none;color:inherit;display:block" },
      poster,
      el("div", { class: "lib-body" },
        el("h3", {}, (p.title || p.project_id).toUpperCase()),
        meta,
        p.stage_states.length ? miniRail(p.stage_states) : null,
      )
    )
  );

  // If there are renders, add a direct playback bar
  if (p.render_count) {
    const playBar = el("div", { style: "padding: 0 14px 12px; display:flex; gap:8px;" },
      el("button", {
        class: "btn-action",
        style: "flex:1; justify-content:center; border-color:var(--green); color:var(--green);",
        onclick: (e) => {
          e.preventDefault();
          e.stopPropagation();
          // Find first render from project state
          getJSON(`/api/project/${p.project_id}/state`).then(st => {
            if (st.media && st.media.renders && st.media.renders.length) {
              playVideo(p.project_id, st.media.renders[0].path, st.media.renders[0].label || p.title);
            } else {
              location.href = `/p/${p.project_id}`;
            }
          });
        }
      }, "▶ Watch Finished Video")
    );
    cardEl.append(playBar);
  }

  return cardEl;
}

// ---- Modals ---------------------------------------------------------------

function showNewProductionModal() {
  const pipelines = (metaInfo && metaInfo.pipelines) || [
    { name: "cinematic", description: "Cinematic film / trailer" },
    { name: "animated-explainer", description: "Explainer with Remotion graphics" },
    { name: "documentary-montage", description: "Montage with archive & real clips" },
    { name: "talking-head", description: "Avatar / presenter video" },
    { name: "clip-factory", description: "Short-form clips extraction" }
  ];
  const playbooks = (metaInfo && metaInfo.playbooks) || [
    "clean-professional", "flat-motion-graphics", "minimalist-diagram", "anime-ghibli", "premium-minimalist"
  ];

  const pipelineOptions = pipelines.map(p => el("option", { value: p.name }, `${p.name} — ${p.description.slice(0, 45)}`));
  const playbookOptions = playbooks.map(s => el("option", { value: s }, s));

  const form = el("form", { onsubmit: (e) => { e.preventDefault(); handleLaunchProduction(); } },
    el("div", { class: "form-group" },
      el("label", {}, "Production Title / Topic"),
      el("input", { class: "form-control", id: "prodTitle", required: "true", value: "The Future of AI Video", placeholder: "e.g. Signal From Tomorrow" })
    ),
    el("div", { class: "form-group" },
      el("label", {}, "Pipeline Architecture"),
      el("select", { class: "form-control form-select", id: "prodPipeline" }, ...pipelineOptions),
      el("div", { class: "form-desc" }, "Each pipeline orchestrates specialized AI agents (Research, Script, Scene Plan, Assets, Edit, Remotion Composer).")
    ),
    el("div", { class: "form-group" },
      el("label", {}, "Visual Style Playbook"),
      el("select", { class: "form-control form-select", id: "prodStyle" }, ...playbookOptions),
      el("div", { class: "form-desc" }, "Defines color palettes, typography rules, animation pacing, and media layout tokens.")
    ),
    el("div", { class: "form-group" },
      el("label", {}, "Execution Mode"),
      el("select", { class: "form-control form-select", id: "prodMode" },
        el("option", { value: "simulate" }, "▶ Interactive Simulation — Watch production happen live on Backlot board (~15s)"),
        el("option", { value: "scaffold" }, "📁 Project Scaffold — Initialize workspace for AI Coding Agent production")
      )
    ),
    el("div", { style: "display:flex; justify-content:flex-end; gap:10px; margin-top:24px;" },
      el("button", { type: "button", class: "btn-action", onclick: closeModal }, "Cancel"),
      el("button", { type: "submit", class: "btn-action primary", id: "btnSubmitProd" }, "🚀 Launch Production")
    )
  );

  const card = el("div", { class: "modal-card" },
    el("h2", {}, "Launch New Production"),
    el("p", { class: "sub" }, "Create a video production project orchestrated by OpenMontage's multi-agent pipelines and Remotion composition engine."),
    form
  );

  openModal(card);
}

async function handleLaunchProduction() {
  const btn = document.getElementById("btnSubmitProd");
  if (btn) { btn.disabled = true; btn.textContent = "Launching…"; }

  const title = document.getElementById("prodTitle").value.trim();
  const pipeline = document.getElementById("prodPipeline").value;
  const style = document.getElementById("prodStyle").value;
  const mode = document.getElementById("prodMode").value;
  const rawId = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 30);
  const projectId = `${rawId}-${Date.now().toString().slice(-4)}`;

  try {
    if (mode === "simulate") {
      const res = await fetch("/api/action/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, title, pipeline, style, fast: true })
      });
      const data = await res.json();
      closeModal();
      setTimeout(() => {
        location.href = `/p/${data.project_id}`;
      }, 1000);
    } else {
      const res = await fetch("/api/action/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, title, pipeline, style })
      });
      const data = await res.json();
      closeModal();
      location.href = `/p/${data.project_id}`;
    }
  } catch (err) {
    alert(`Failed to launch: ${err.message}`);
    if (btn) { btn.disabled = false; btn.textContent = "🚀 Launch Production"; }
  }
}

function showToolsMatrixModal() {
  const providers = (metaInfo && metaInfo.providers) || {};
  const sys = (metaInfo && metaInfo.system) || {};

  const items = Object.entries(providers).map(([key, active]) => {
    return el("div", { class: `provider-item ${active ? "active" : ""}` },
      el("span", {}, key),
      el("span", { style: active ? "color:var(--green);font-weight:600" : "color:var(--text-3)" }, active ? "CONFIGURED ✓" : "OPTIONAL")
    );
  });

  const card = el("div", { class: "modal-card" },
    el("h2", {}, "Tools, Models & Providers Matrix"),
    el("p", { class: "sub" }, "OpenMontage integrates 100+ tools across local GPU and cloud AI providers. Zero-key pipelines (Remotion, Piper-TTS, FFmpeg) work completely offline for free!"),
    el("div", { style: "margin-bottom:14px; padding:12px; background:var(--surface-2); border-radius:6px; font-family:var(--mono); font-size:12px;" },
      el("div", {}, `● Python Runtime: ${sys.python || "3.14"} (active)`),
      el("div", {}, `● Node.js Runtime: ${sys.node ? "Detected ✓" : "Missing"}`),
      el("div", {}, `● FFmpeg Encoder: ${sys.ffmpeg ? "Available ✓" : "Missing"}`),
      el("div", {}, `● Piper-TTS Voice: Local ONNX Engine (Installed ✓)`),
      el("div", {}, `● Remotion Studio: http://localhost:3000 (Running ✓)`),
    ),
    el("h3", { style: "font-family:var(--mono);font-size:13px;letter-spacing:.05em;color:var(--text-2);text-transform:uppercase;margin:16px 0 8px 0;" }, "Cloud AI API Gateways (.env):"),
    el("div", { class: "provider-grid" }, ...items),
    el("p", { class: "form-desc", style: "line-height:1.6;" }, "To enable more providers (FLUX, Kling, Google Veo, ElevenLabs, OpenAI), add your keys to the <code>.env</code> file in the repository root."),
    el("div", { style: "display:flex; justify-content:flex-end; margin-top:20px;" },
      el("button", { class: "btn-action primary", onclick: closeModal }, "Got It")
    )
  );

  openModal(card);
}

function showDemosModal() {
  const demos = (metaInfo && metaInfo.demos) || [
    { name: "focusflow-pitch", rendered: true },
    { name: "code-to-screen", rendered: false },
    { name: "world-in-numbers", rendered: false }
  ];

  const demoCards = demos.map(d => {
    return el("div", { style: "display:flex; justify-content:space-between; align-items:center; padding:12px 16px; background:var(--surface-2); border:1px solid var(--border); border-radius:8px; margin-bottom:10px;" },
      el("div", {},
        el("div", { style: "font-family:var(--mono); font-weight:600; color:var(--text);" }, d.name),
        el("div", { style: "font-size:11px; color:var(--text-3);" }, d.rendered ? "Rendered MP4 ready in projects/demos/renders/" : "Zero-key Remotion React composition")
      ),
      el("div", { style: "display:flex; gap:8px;" },
        d.rendered
          ? el("button", { class: "btn-action primary", onclick: () => playVideo("demos", `renders/${d.name}.mp4`, d.name) }, "▶ Play MP4")
          : el("a", { class: "btn-action", href: "http://localhost:3000", target: "_blank" }, "Preview in Studio ↗")
      )
    );
  });

  const card = el("div", { class: "modal-card" },
    el("h2", {}, "Curated Zero-Key Remotion Demos"),
    el("p", { class: "sub" }, "These full-featured explainer videos demonstrate OpenMontage's React motion-graphics engine without requiring any paid API keys:"),
    el("div", {}, ...demoCards),
    el("div", { style: "margin-top:20px; display:flex; justify-content:space-between; align-items:center;" },
      el("a", { href: "http://localhost:3000", target: "_blank", class: "btn-action" }, "Open Remotion Studio ↗"),
      el("button", { class: "btn-action primary", onclick: closeModal }, "Close")
    )
  );

  openModal(card);
}

// ---- Event Listeners ------------------------------------------------------

document.getElementById("btnNewProduction")?.addEventListener("click", showNewProductionModal);
document.getElementById("btnToolsMatrix")?.addEventListener("click", showToolsMatrixModal);
document.getElementById("btnDemos")?.addEventListener("click", showDemosModal);

// ---- Render Library -------------------------------------------------------

async function render() {
  try {
    metaInfo = await getJSON("/api/meta/info");
  } catch (e) {
    console.warn("Could not load meta info:", e);
  }

  const projects = await getJSON("/api/projects");
  document.getElementById("count").textContent = `${projects.length} project${projects.length === 1 ? "" : "s"}`;
  const liveCount = projects.filter((p) => p.live).length;
  const badge = document.getElementById("liveBadge");
  badge.classList.toggle("idle", liveCount === 0);
  document.getElementById("liveText").textContent = liveCount ? `${liveCount} LIVE` : "IDLE";
  
  grid.innerHTML = "";
  document.getElementById("empty").style.display = projects.length ? "none" : "block";
  for (const p of projects) grid.append(card(p));
}

render().catch(console.error);

if (!new URLSearchParams(location.search).has("static")) {
  subscribe("/api/library/events", () => render().catch(console.error));
}
