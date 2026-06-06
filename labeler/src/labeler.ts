// labeler.ts — segment model, validation, nudge, CSV in/out.
// Pure logic: knows nothing about the DOM (ui.ts does the wiring).
// The slicing pipeline can import these same types/rules later.

export const AD_TYPES = ["commercial", "promo", "sponsored", "other"] as const;
export type AdType = (typeof AD_TYPES)[number];
export const DEFAULT_TYPE: AdType = "commercial";

/** Nudge step for correcting a delayed click (locked: 0.5s). */
export const NUDGE_STEP = 0.5;

export interface Segment {
  /** seconds — raw seconds are the storage format; mm:ss is display-only */
  start: number;
  end: number;
  type: AdType;
}

export function isAdType(value: string): value is AdType {
  return (AD_TYPES as readonly string[]).includes(value);
}

/** Returns an error message, or null if the segment is valid. */
export function validateSegment(start: number, end: number): string | null {
  if (!Number.isFinite(start) || !Number.isFinite(end)) return "start and end must be numbers";
  if (start < 0 || end < 0) return "times must be ≥ 0";
  if (end <= start) return "end must be after start";
  return null;
}

/** ±NUDGE_STEP, clamped at 0, rounded to 0.1s to avoid float noise. */
export function nudge(value: number, direction: 1 | -1): number {
  return Math.max(0, Math.round((value + direction * NUDGE_STEP) * 10) / 10);
}

/** Display format mm:ss.s (or h:mm:ss.s). Storage stays raw seconds. */
export function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = (seconds % 60).toFixed(1).padStart(4, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

/** Accepts raw seconds ("134.5") or clock-style ("2:14.5", "1:02:14"). */
export function parseTimeInput(text: string): number | null {
  const trimmed = text.trim();
  if (trimmed === "") return null;
  if (/^\d+(\.\d+)?$/.test(trimmed)) return parseFloat(trimmed);
  const m = trimmed.match(/^(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)$/);
  if (!m) return null;
  const [, hh, mm, ss] = m;
  return (hh ? parseInt(hh, 10) * 3600 : 0) + parseInt(mm, 10) * 60 + parseFloat(ss);
}

export class SegmentStore {
  private segments: Segment[] = [];

  list(): readonly Segment[] {
    return this.segments;
  }

  /** Validates and inserts, keeping the list sorted by start. Returns error or null. */
  add(start: number, end: number, type: AdType): string | null {
    const err = validateSegment(start, end);
    if (err) return err;
    this.segments.push({ start, end, type });
    this.segments.sort((a, b) => a.start - b.start);
    return null;
  }

  /** Inline edit. Returns error or null; invalid edits leave the row unchanged. */
  update(index: number, patch: Partial<Segment>): string | null {
    const cur = this.segments[index];
    if (!cur) return "no such row";
    const next = { ...cur, ...patch };
    const err = validateSegment(next.start, next.end);
    if (err) return err;
    this.segments[index] = next;
    this.segments.sort((a, b) => a.start - b.start);
    return null;
  }

  remove(index: number): void {
    this.segments.splice(index, 1);
  }

  clear(): void {
    this.segments = [];
  }

  /** CSV: ad_start,ad_end,type,source — times in raw seconds (machine-friendly). */
  toCSV(source: string): string {
    const rows = this.segments.map(
      (s) => `${s.start},${s.end},${s.type},${source}`,
    );
    return ["ad_start,ad_end,type,source", ...rows].join("\n") + "\n";
  }
}

export interface CSVImport {
  segments: Segment[];
  /** source MP4 filename found in the file (null if none) */
  source: string | null;
  /** per-line problems; valid lines still import */
  errors: string[];
}

export function parseCSV(text: string): CSVImport {
  const out: CSVImport = { segments: [], source: null, errors: [] };
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (i === 0 && /^ad_start\s*,/i.test(line)) continue; // header
    const cols = line.split(",").map((c) => c.trim());
    if (cols.length < 3) {
      out.errors.push(`line ${i + 1}: expected ad_start,ad_end,type[,source]`);
      continue;
    }
    const start = parseFloat(cols[0]);
    const end = parseFloat(cols[1]);
    const type = cols[2];
    const err = validateSegment(start, end);
    if (err) {
      out.errors.push(`line ${i + 1}: ${err}`);
      continue;
    }
    if (!isAdType(type)) {
      out.errors.push(`line ${i + 1}: unknown type "${type}"`);
      continue;
    }
    if (cols[3]) out.source = cols[3];
    out.segments.push({ start, end, type });
  }
  out.segments.sort((a, b) => a.start - b.start);
  return out;
}
