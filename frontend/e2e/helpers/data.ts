/** Deterministic JSONL spike (mirrors backend tests `test_analysis._recent_jsonl_spike`). */
export function buildRecentJsonlSpike(): Buffer {
  const now = new Date();
  const lines: string[] = [];

  const toIso = (d: Date) => d.toISOString().replace("+00:00", "Z").replace(".000Z", "Z");

  for (let hour = 1; hour < 8; hour++) {
    const ts = toIso(new Date(now.getTime() - hour * 60 * 60 * 1000));
    for (let i = 0; i < 15; i++) {
      lines.push(JSON.stringify({ timestamp: ts, level: "INFO", message: "steady traffic" }));
    }
    lines.push(JSON.stringify({ timestamp: ts, level: "ERROR", message: "baseline error" }));
  }
  const latest = toIso(now);
  for (let i = 0; i < 30; i++) {
    lines.push(
      JSON.stringify({ timestamp: latest, level: "ERROR", message: "database connection reset" })
    );
  }
  for (let i = 0; i < 5; i++) {
    lines.push(JSON.stringify({ timestamp: latest, level: "CRITICAL", message: "database unavailable" }));
  }
  return Buffer.from(`${lines.join("\n")}\n`, "utf-8");
}