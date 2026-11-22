import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, Download, Loader2, Search, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { SectionPanel } from "@/components/incidents/SectionPanel";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { ApiError } from "@/services/api";
import { getInvestigationReport, listRootCauses, runInvestigation } from "@/services/rca";
import type { RootCauseCandidate } from "@/types/rca";
import { formatDateTime } from "@/utils/formatDate";

function EvidenceStrengthBar({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, score));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-wide text-slate-500">
        <span>Evidence strength</span>
        <span className="tabular-nums text-slate-300">{clamped.toFixed(1)} / 100</span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-graphite-800"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        aria-label={`Evidence strength score ${clamped.toFixed(1)} out of 100, not a probability`}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-indigo to-accent-cyan transition-all"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <p className="text-[10px] text-slate-600">Weighted score — not calibrated probability.</p>
    </div>
  );
}

function EvidenceList({
  items,
  stance,
}: {
  items: Array<Record<string, unknown>>;
  stance: "supporting" | "contradicting";
}) {
  const filtered = items.filter((row) => row.stance === stance);
  if (filtered.length === 0) {
    return <p className="text-xs text-slate-500">No {stance} items recorded.</p>;
  }
  const tone =
    stance === "supporting"
      ? "border-emerald-500/25 bg-emerald-500/5"
      : "border-rose-500/25 bg-rose-500/5";
  const icon =
    stance === "supporting" ? (
      <ThumbsUp className="h-3.5 w-3.5 text-emerald-400" aria-hidden />
    ) : (
      <ThumbsDown className="h-3.5 w-3.5 text-rose-400" aria-hidden />
    );

  return (
    <ul className="space-y-2">
      {filtered.map((row, index) => (
        <li
          key={`${String(row.evidence_key ?? index)}-${stance}`}
          className={cn("rounded-md border px-3 py-2 text-xs leading-relaxed text-slate-300", tone)}
        >
          <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-500">
            {icon}
            <span>
              {String(row.source_type ?? "source")}
              {row.source_id ? ` · ${String(row.source_id).slice(0, 8)}…` : ""}
            </span>
            {row.timestamp ? (
              <span className="normal-case text-slate-600">{formatDateTime(String(row.timestamp))}</span>
            ) : null}
          </div>
          <p>{String(row.explanation ?? "")}</p>
        </li>
      ))}
    </ul>
  );
}

export function IncidentRcaSection({
  projectId,
  incidentId,
}: {
  projectId: string;
  incidentId: string;
}) {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const candidatesQuery = useQuery({
    queryKey: ["root-causes", projectId, incidentId],
    queryFn: () => listRootCauses(projectId, incidentId),
  });

  const reportQuery = useQuery({
    queryKey: ["investigation-report", projectId, incidentId],
    queryFn: () => getInvestigationReport(projectId, incidentId),
    enabled: (candidatesQuery.data?.items?.length ?? 0) > 0,
  });

  const investigateMutation = useMutation({
    mutationFn: () => runInvestigation(projectId, incidentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["root-causes", projectId, incidentId] });
      queryClient.invalidateQueries({ queryKey: ["investigation-report", projectId, incidentId] });
    },
  });

  const items = candidatesQuery.data?.items ?? [];

  useEffect(() => {
    const first = items[0];
    if (!selectedId && first) {
      setSelectedId(first.id);
    }
  }, [items, selectedId]);

  const selected: RootCauseCandidate | undefined = items.find((item) => item.id === selectedId);

  const evidenceItems = useMemo(
    () => selected?.evidence_summary?.items ?? [],
    [selected]
  );

  const exportMarkdown = () => {
    if (!reportQuery.data?.markdown) {
      return;
    }
    const blob = new Blob([reportQuery.data.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `incident-${incidentId}-report.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const report = reportQuery.data?.report;
  const investigationVersion =
    investigateMutation.data?.version ?? candidatesQuery.data?.version ?? null;
  const investigationStatus = candidatesQuery.data?.status ?? investigateMutation.data?.status;

  return (
    <div className="space-y-4" aria-label="Root cause analysis">
      <SectionPanel
        id="rca-controls"
        title="Root cause analysis"
        description="Evidence-based ranking — scores reflect strength of support, not likelihood."
      >
        <div className="space-y-4">
          <p className="text-xs leading-relaxed text-slate-500">{candidatesQuery.data?.score_note}</p>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              onClick={() => investigateMutation.mutate()}
              disabled={investigateMutation.isPending}
              aria-busy={investigateMutation.isPending}
            >
              {investigateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
                  Running investigation…
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" aria-hidden />
                  Run RCA investigation
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={exportMarkdown}
              disabled={!reportQuery.data?.markdown}
            >
              <Download className="mr-2 h-4 w-4" aria-hidden />
              Export Markdown
            </Button>
          </div>

          {investigateMutation.isError ? (
            <p className="flex items-start gap-2 text-sm text-rose-300/90" role="alert">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              {investigateMutation.error instanceof ApiError
                ? investigateMutation.error.message
                : "Investigation failed. Check logs and try again."}
            </p>
          ) : null}

          <dl className="grid gap-3 text-xs sm:grid-cols-3">
            <div className="rounded-md border border-graphite-700 bg-graphite-850/50 px-3 py-2">
              <dt className="text-slate-500">Investigation version</dt>
              <dd className="mt-0.5 font-medium text-slate-200">
                {investigationVersion != null ? `v${investigationVersion}` : "—"}
              </dd>
            </div>
            <div className="rounded-md border border-graphite-700 bg-graphite-850/50 px-3 py-2">
              <dt className="text-slate-500">Status</dt>
              <dd className="mt-0.5 font-medium text-slate-200">{investigationStatus ?? "—"}</dd>
            </div>
            <div className="rounded-md border border-graphite-700 bg-graphite-850/50 px-3 py-2">
              <dt className="text-slate-500">Candidates</dt>
              <dd className="mt-0.5 font-medium text-slate-200">{items.length}</dd>
            </div>
          </dl>

          {investigateMutation.data ? (
            <p className="text-sm text-slate-400">
              Completed · {investigateMutation.data.candidate_count} candidates · top hypothesis:{" "}
              <span className="text-slate-200">
                {investigateMutation.data.top_candidate_title ?? "—"}
              </span>{" "}
              ({investigateMutation.data.top_confidence_score.toFixed(1)} evidence strength)
            </p>
          ) : null}

          {candidatesQuery.data?.status === "insufficient_data" ? (
            <p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm text-amber-200/90">
              Insufficient evidence for strong hypotheses. Import more logs or run analysis first.
            </p>
          ) : null}
        </div>
      </SectionPanel>

      <div className="grid gap-4 xl:grid-cols-5">
        <SectionPanel
          id="rca-candidates"
          title="Ranked candidates"
          description="Higher rank = stronger supporting evidence after penalties."
          className="xl:col-span-2"
        >
          {candidatesQuery.isLoading ? (
            <p className="text-sm text-slate-500" aria-live="polite">
              Loading candidates…
            </p>
          ) : null}
          {items.length === 0 && !candidatesQuery.isLoading ? (
            <p className="text-sm text-slate-500">No candidates yet. Run an investigation.</p>
          ) : null}
          <div className="space-y-2" role="listbox" aria-label="Root cause candidates">
            {items.map((item) => {
              const active = selectedId === item.id;
              const isTop = item.ranking === 1;
              return (
                <button
                  key={item.id}
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => setSelectedId(item.id)}
                  className={cn(
                    "w-full rounded-lg border px-3 py-3 text-left transition-colors",
                    active
                      ? "border-accent-cyan/40 bg-accent-indigo/10 ring-1 ring-accent-indigo/20"
                      : "border-graphite-700 hover:border-graphite-600 hover:bg-graphite-850/40",
                    isTop && !active && "border-graphite-600"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="text-sm font-medium text-slate-100">
                        <span className="text-slate-500">#{item.ranking}</span> {item.title}
                      </p>
                      <p className="text-[10px] uppercase tracking-wide text-slate-500">
                        {item.cause_type.replaceAll("_", " ")}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-lg font-semibold tabular-nums text-slate-100">
                        {item.confidence_score.toFixed(1)}
                      </p>
                      <p className="text-[10px] text-slate-500">strength</p>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-slate-500">
                    <span className="text-emerald-400/90">+{item.supporting_evidence_count} supporting</span>
                    <span className="text-rose-400/90">−{item.contradicting_evidence_count} contradicting</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-xs text-slate-400">{item.explanation}</p>
                </button>
              );
            })}
          </div>
        </SectionPanel>

        <SectionPanel
          id="rca-detail"
          title="Candidate detail"
          description="Trace conclusions to source records."
          className="xl:col-span-3"
        >
          {!selected ? (
            <p className="text-sm text-slate-500">Select a candidate to inspect evidence.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <h4 className="text-base font-semibold text-slate-100">{selected.title}</h4>
                <p className="mt-1 text-sm leading-relaxed text-slate-300">{selected.explanation}</p>
              </div>
              <EvidenceStrengthBar score={selected.confidence_score} />
              <p className="text-xs text-slate-500">{selected.evidence_summary.score_note}</p>

              <div className="grid gap-4 lg:grid-cols-2">
                <div>
                  <h5 className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-400/90">
                    Supporting evidence
                  </h5>
                  <EvidenceList items={evidenceItems} stance="supporting" />
                </div>
                <div>
                  <h5 className="mb-2 text-xs font-semibold uppercase tracking-wide text-rose-400/90">
                    Contradicting evidence
                  </h5>
                  <EvidenceList items={evidenceItems} stance="contradicting" />
                </div>
              </div>

              <dl className="grid gap-2 border-t border-graphite-800 pt-3 text-xs sm:grid-cols-2">
                {selected.service_id ? (
                  <div>
                    <dt className="text-slate-500">Related service</dt>
                    <dd className="font-mono text-slate-300">{selected.service_id}</dd>
                  </div>
                ) : null}
                {selected.deployment_id ? (
                  <div>
                    <dt className="text-slate-500">Related deployment</dt>
                    <dd className="font-mono text-slate-300">{selected.deployment_id}</dd>
                  </div>
                ) : null}
              </dl>
            </div>
          )}
        </SectionPanel>
      </div>

      {report ? (
        <SectionPanel id="rca-report" title="Investigation report" description="Structured summary from the engine.">
          <div className="space-y-6 text-sm">
            {report.executive_summary ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Executive summary
                </h4>
                <p className="mt-2 leading-relaxed text-slate-300">{String(report.executive_summary)}</p>
              </section>
            ) : null}

            {typeof report.investigation_conclusion === "string" ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Conclusion</h4>
                <p className="mt-2 text-slate-300">{report.investigation_conclusion}</p>
              </section>
            ) : null}

            {report.incident_overview && typeof report.incident_overview === "object" ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Incident overview
                </h4>
                <Card className="mt-2 border-graphite-700 bg-graphite-850/30">
                  <CardBody className="grid gap-2 text-xs sm:grid-cols-2">
                    {Object.entries(report.incident_overview as Record<string, unknown>).map(([key, value]) => (
                      <div key={key}>
                        <p className="text-slate-500">{key.replaceAll("_", " ")}</p>
                        <p className="text-slate-300">
                          {typeof value === "object" ? JSON.stringify(value) : String(value)}
                        </p>
                      </div>
                    ))}
                  </CardBody>
                </Card>
              </section>
            ) : null}

            {Array.isArray(report.root_cause_candidates) && report.root_cause_candidates.length > 0 ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Ranked hypotheses (report)
                </h4>
                <ul className="mt-2 space-y-2">
                  {(report.root_cause_candidates as Array<Record<string, unknown>>).slice(0, 5).map((row) => (
                    <li
                      key={String(row.title)}
                      className="rounded-md border border-graphite-700 px-3 py-2 text-xs text-slate-300"
                    >
                      #{String(row.ranking)} {String(row.title)} — strength {String(row.confidence_score)}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {Array.isArray(report.limitations) && report.limitations.length > 0 ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Limitations</h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-400">
                  {(report.limitations as string[]).map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </section>
            ) : null}

            {Array.isArray(report.recommended_next_steps) ? (
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Recommended next steps
                </h4>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-400">
                  {(report.recommended_next_steps as string[]).map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
        </SectionPanel>
      ) : null}
    </div>
  );
}