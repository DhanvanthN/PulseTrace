import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionPanel } from "@/components/incidents/SectionPanel";
import { SeverityBadge } from "@/components/incidents/SeverityBadge";
import { StatusBadge } from "@/components/incidents/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { IncidentRcaSection } from "@/features/incidents/IncidentRcaSection";
import {
  addIncidentNote,
  getIncident,
  getIncidentEvidence,
  getIncidentTimeline,
  listDeployments,
  updateIncident,
} from "@/services/incidents";
import { cn } from "@/lib/cn";
import { TIMELINE_EVENT_META } from "@/utils/severity";
import { formatDateTime, formatRelative } from "@/utils/formatDate";
import { AlertTriangle, Clock, FileText, Loader2 } from "lucide-react";

export function IncidentDetailPage() {
  const { projectId, incidentId } = useParams<{ projectId: string; incidentId: string }>();
  useDocumentTitle("Incident investigation · PulseTrace");
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const incidentQuery = useQuery({
    queryKey: ["incident", projectId, incidentId],
    queryFn: () => getIncident(projectId ?? "", incidentId ?? ""),
    enabled: Boolean(projectId && incidentId),
  });

  const timelineQuery = useQuery({
    queryKey: ["incident-timeline", projectId, incidentId],
    queryFn: () => getIncidentTimeline(projectId ?? "", incidentId ?? ""),
    enabled: Boolean(projectId && incidentId),
  });

  const evidenceQuery = useQuery({
    queryKey: ["incident-evidence", projectId, incidentId],
    queryFn: () => getIncidentEvidence(projectId ?? "", incidentId ?? ""),
    enabled: Boolean(projectId && incidentId),
  });

  const deploymentsQuery = useQuery({
    queryKey: ["deployments", projectId],
    queryFn: () => listDeployments(projectId ?? ""),
    enabled: Boolean(projectId),
  });

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateIncident(projectId ?? "", incidentId ?? "", { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", projectId, incidentId] });
      queryClient.invalidateQueries({ queryKey: ["incident-timeline", projectId, incidentId] });
    },
  });

  const noteMutation = useMutation({
    mutationFn: () => addIncidentNote(projectId ?? "", incidentId ?? "", note),
    onSuccess: () => {
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["incident-timeline", projectId, incidentId] });
    },
  });

  const incident = incidentQuery.data;
  const deploymentEvents = timelineQuery.data?.items.filter((e) => e.event_type === "DEPLOYMENT") ?? [];
  const relatedDeployments = deploymentsQuery.data?.items.filter((d) =>
    deploymentEvents.some((e) => String(e.metadata.deployment_id ?? "") === d.id)
  );

  const anomalyEvidence = evidenceQuery.data?.items.filter((row) => row.evidence_type.includes("anomaly")) ?? [];
  const otherEvidence = evidenceQuery.data?.items.filter((row) => !row.evidence_type.includes("anomaly")) ?? [];

  if (incidentQuery.isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500" aria-live="polite">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        Loading incident…
      </div>
    );
  }

  if (incidentQuery.isError || !incident) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Incident unavailable"
        description="This incident could not be loaded. It may have been removed or you may not have access."
      />
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title={incident.title}
        description={incident.description || "Correlated incident — review timeline and evidence before RCA."}
        breadcrumb={{
          label: "Incident dashboard",
          to: `/projects/${projectId}/incidents`,
        }}
        actions={
          <>
            <Button
              type="button"
              variant="secondary"
              onClick={() => statusMutation.mutate("INVESTIGATING")}
              disabled={statusMutation.isPending}
            >
              Mark investigating
            </Button>
            <Button type="button" onClick={() => statusMutation.mutate("RESOLVED")} disabled={statusMutation.isPending}>
              Resolve
            </Button>
            <Button type="button" variant="secondary" onClick={() => statusMutation.mutate("OPEN")}>
              Reopen
            </Button>
          </>
        }
      />

      <section aria-label="Incident overview" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Severity</p>
          <div className="mt-2">
            <SeverityBadge severity={incident.severity} />
          </div>
        </div>
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Status</p>
          <div className="mt-2">
            <StatusBadge status={incident.status} />
          </div>
        </div>
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Started</p>
          <p className="mt-1 text-sm text-slate-200">{formatDateTime(incident.started_at)}</p>
          <p className="text-xs text-slate-500">{formatRelative(incident.started_at)}</p>
        </div>
        <div className="rounded-lg border border-graphite-700 bg-graphite-900 px-4 py-3">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Activity</p>
          <p className="mt-1 text-sm text-slate-200">
            {incident.events_count} events · {incident.evidence_count} evidence
          </p>
          <p className="text-xs text-slate-500">Last {formatRelative(incident.last_activity_at)}</p>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-5">
        <SectionPanel
          id="incident-timeline"
          title="Incident timeline"
          description="Temporal correlation only — not proof of causation."
          className="lg:col-span-2"
        >
          {timelineQuery.isLoading ? <p className="text-sm text-slate-500">Loading timeline…</p> : null}
          {!timelineQuery.isLoading && (timelineQuery.data?.items.length ?? 0) === 0 ? (
            <p className="text-sm text-slate-500">No timeline events yet.</p>
          ) : null}
          <ol className="relative space-y-0 border-l border-graphite-700 pl-4">
            {timelineQuery.data?.items.map((event) => {
              const meta = TIMELINE_EVENT_META[event.event_type] ?? {
                label: event.event_type,
                border: "border-graphite-600",
                iconColor: "text-slate-400",
              };
              return (
                <li key={event.id} className="relative pb-4 last:pb-0">
                  <span
                    className="absolute -left-[1.3rem] mt-1 h-2.5 w-2.5 rounded-full border-2 border-graphite-950 bg-graphite-600 ring-2 ring-graphite-950"
                    aria-hidden
                  />
                  <div
                    className={cn(
                      "rounded-lg border-l-2 bg-graphite-850/40 px-3 py-2",
                      meta.border
                    )}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className={cn("text-[10px] font-medium uppercase tracking-wide", meta.iconColor)}>
                        {meta.label}
                      </p>
                      <p className="flex items-center gap-1 text-[10px] text-slate-500">
                        <Clock className="h-3 w-3" aria-hidden />
                        {formatDateTime(event.event_timestamp)}
                      </p>
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-slate-200">{event.description}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        </SectionPanel>

        <div className="space-y-4 lg:col-span-3">
          <SectionPanel
            id="related-anomalies"
            title="Related anomalies"
            description="Signals linked during correlation."
          >
            {anomalyEvidence.length === 0 ? (
              <p className="text-sm text-slate-500">No anomaly evidence linked.</p>
            ) : (
              <ul className="space-y-2">
                {anomalyEvidence.map((row) => (
                  <li key={row.id} className="rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm">
                    <p className="text-[10px] uppercase text-amber-200/80">{row.evidence_type}</p>
                    <p className="text-slate-200">{row.explanation}</p>
                    {row.anomaly_id ? (
                      <p className="mt-1 font-mono text-[10px] text-slate-500">anomaly {row.anomaly_id}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </SectionPanel>

          <SectionPanel id="supporting-evidence" title="Supporting evidence">
            {otherEvidence.length === 0 && anomalyEvidence.length === 0 ? (
              <p className="text-sm text-slate-500">No evidence records yet.</p>
            ) : (
              <ul className="space-y-2">
                {otherEvidence.map((row) => (
                  <li
                    key={row.id}
                    className="rounded-md border border-graphite-700 bg-graphite-900/60 px-3 py-2 text-sm"
                  >
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-500">
                      <FileText className="h-3 w-3" aria-hidden />
                      {row.evidence_type}
                    </div>
                    <p className="mt-1 text-slate-200">{row.explanation}</p>
                    <p className="mt-1 font-mono text-[10px] text-slate-600">
                      {row.anomaly_id ? `anomaly ${row.anomaly_id}` : null}
                      {row.cluster_id ? ` · cluster ${row.cluster_id}` : null}
                      {row.log_id ? ` · log ${row.log_id}` : null}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </SectionPanel>

          <SectionPanel
            id="deployments"
            title="Deployment information"
            description="Temporal overlap — not verified root cause."
          >
            {relatedDeployments?.length ? (
              <ul className="space-y-2 text-sm">
                {relatedDeployments.map((d) => (
                  <li
                    key={d.id}
                    className="rounded-md border border-indigo-500/20 bg-indigo-500/5 px-3 py-2 text-slate-300"
                  >
                    <p className="font-medium text-slate-100">v{d.version}</p>
                    <p className="text-xs text-slate-500">
                      {formatDateTime(d.deployed_at)} · {d.change_type}
                    </p>
                    <p className="mt-1 text-sm text-slate-400">{d.description || "No description"}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No deployment events linked on this timeline.</p>
            )}
          </SectionPanel>

          <SectionPanel id="investigation-notes" title="Investigation notes">
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (note.trim()) noteMutation.mutate();
              }}
            >
              <Input
                label="Add note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Document observations for the timeline…"
              />
              <Button type="submit" disabled={!note.trim() || noteMutation.isPending}>
                {noteMutation.isPending ? "Saving…" : "Add note"}
              </Button>
            </form>
          </SectionPanel>
        </div>
      </div>

      {projectId && incidentId ? (
        <IncidentRcaSection projectId={projectId} incidentId={incidentId} />
      ) : null}
    </div>
  );
}