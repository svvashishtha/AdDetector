// ui.ts — DOM wiring only. All segment logic lives in labeler.ts.

import {
  AD_TYPES,
  AdType,
  DEFAULT_TYPE,
  SegmentStore,
  formatTime,
  nudge,
  parseCSV,
  parseTimeInput,
  validateSegment,
} from "./labeler";

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el as T;
};

const video = $<HTMLVideoElement>("video");
const fileInput = $<HTMLInputElement>("file-input");
const filenameEl = $<HTMLElement>("filename");
const startField = $<HTMLInputElement>("start-field");
const endField = $<HTMLInputElement>("end-field");
const typeSelect = $<HTMLSelectElement>("type-select");
const statusEl = $<HTMLElement>("status");
const tbody = $<HTMLTableSectionElement>("segments-body");
const importInput = $<HTMLInputElement>("import-input");

const store = new SegmentStore();
let sourceName = "";

// ---------------------------------------------------------------- helpers

function setStatus(msg: string, isError = false): void {
  statusEl.textContent = msg;
  statusEl.className = isError ? "status error" : "status";
}

function fieldValue(field: HTMLInputElement): number | null {
  return parseTimeInput(field.value);
}

function download(name: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

function csvName(): string {
  return sourceName ? sourceName.replace(/\.[^.]+$/, "") + ".csv" : "labels.csv";
}

// ---------------------------------------------------------------- segment table

function render(): void {
  tbody.innerHTML = "";
  store.list().forEach((seg, i) => {
    const tr = document.createElement("tr");

    for (const key of ["start", "end"] as const) {
      const td = document.createElement("td");
      const input = document.createElement("input");
      input.type = "text";
      input.value = String(seg[key]);
      input.title = formatTime(seg[key]);
      input.className = "time-edit";
      input.addEventListener("change", () => {
        const v = parseTimeInput(input.value);
        const err = v === null ? "not a time" : store.update(i, { [key]: v });
        if (err) {
          setStatus(`row ${i + 1}: ${err}`, true);
        } else {
          setStatus("");
        }
        render();
      });
      td.appendChild(input);

      const jump = document.createElement("button");
      jump.textContent = formatTime(seg[key]);
      jump.className = "jump";
      jump.title = "jump video here to verify";
      jump.addEventListener("click", () => {
        video.currentTime = seg[key];
        video.pause();
      });
      td.appendChild(jump);
      tr.appendChild(td);
    }

    const typeTd = document.createElement("td");
    const sel = document.createElement("select");
    for (const t of AD_TYPES) {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      opt.selected = t === seg.type;
      sel.appendChild(opt);
    }
    sel.addEventListener("change", () => {
      store.update(i, { type: sel.value as AdType });
      render();
    });
    typeTd.appendChild(sel);
    tr.appendChild(typeTd);

    const delTd = document.createElement("td");
    const del = document.createElement("button");
    del.textContent = "✕";
    del.title = "delete row";
    del.addEventListener("click", () => {
      store.remove(i);
      render();
    });
    delTd.appendChild(del);
    tr.appendChild(delTd);

    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------- wiring

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  video.src = URL.createObjectURL(file); // stays local — no upload
  sourceName = file.name;
  filenameEl.textContent = file.name;
  setStatus(`loaded ${file.name}`);
});

$("mark-start").addEventListener("click", () => {
  startField.value = video.currentTime.toFixed(1);
});
$("mark-end").addEventListener("click", () => {
  endField.value = video.currentTime.toFixed(1);
});

for (const [id, field, dir] of [
  ["start-minus", startField, -1],
  ["start-plus", startField, 1],
  ["end-minus", endField, -1],
  ["end-plus", endField, 1],
] as const) {
  $(id).addEventListener("click", () => {
    const v = fieldValue(field);
    if (v !== null) field.value = String(nudge(v, dir));
  });
}

$("save-ad").addEventListener("click", () => {
  const start = fieldValue(startField);
  const end = fieldValue(endField);
  if (start === null || end === null) {
    setStatus("mark (or type) both start and end first", true);
    return;
  }
  const err =
    validateSegment(start, end) ?? store.add(start, end, typeSelect.value as AdType);
  if (err) {
    setStatus(err, true);
    return;
  }
  // clear so the next ad starts clean (prevents duplicate marks)
  startField.value = "";
  endField.value = "";
  typeSelect.value = DEFAULT_TYPE;
  setStatus(`saved ${formatTime(start)} → ${formatTime(end)}`);
  render();
});

$("export-csv").addEventListener("click", () => {
  if (store.list().length === 0) {
    setStatus("nothing to export", true);
    return;
  }
  if (!sourceName) {
    setStatus("load the video first so the CSV records its source filename", true);
    return;
  }
  download(csvName(), store.toCSV(sourceName));
  setStatus(`exported ${csvName()}`);
});

$("import-csv").addEventListener("click", () => importInput.click());
importInput.addEventListener("change", async () => {
  const file = importInput.files?.[0];
  if (!file) return;
  const result = parseCSV(await file.text());
  store.clear();
  for (const seg of result.segments) store.add(seg.start, seg.end, seg.type);
  if (result.source && sourceName && result.source !== sourceName) {
    setStatus(
      `warning: CSV is for "${result.source}" but loaded video is "${sourceName}"`,
      true,
    );
  } else {
    const errs = result.errors.length ? ` (${result.errors.length} bad lines skipped)` : "";
    setStatus(`imported ${result.segments.length} segments${errs}`, result.errors.length > 0);
  }
  importInput.value = "";
  render();
});

render();
