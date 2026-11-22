import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { PageHeader } from "@/components/common/PageHeader";
import { SeverityBadge } from "@/components/incidents/SeverityBadge";
import { StatusBadge } from "@/components/incidents/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { correlateIncidents, listIncidents } from "@/services/incidents";
import { formatRelative } from "@/utils/formatDate";
export function IncidentDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Incident dashboard · PulseTrace");
  const queryClient = useQueryClient();

  const incidentsQuery = useQuery({
    queryKey: ["incidents", projectId, "dashboard"],
    queryFn: () => listIncidents(projectId ?? "", { limit: 8 }),
    enabled: Boolean(projectId),
  });

  const correlateMutation = useMutation({
    mutationFn: () => correlateIncidents(projectId ?? ""),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incidents", projectId] }),
  });

  const severityData = Object.entries(incidentsQuery.data?.severity_counts ?? {}).map(([severity, count]) => ({
    severity,
    count,
    fill:
      {
        CRITICAL: "#f43f5e",
        HIGH: "#f97316",
        MEDIUM: "#f59e0b",
        LOW: "#64748b",
      }[severity] ?? "#6366f1",
  }));

  const statusData = Object.entries(incidentsQuery.data?.status_counts ?? {}).map(([status, count]) => ({
    status,
    count,
  }));

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Incident dashboard"
        description="Correlate anomalies into incidents and review project activity."
        breadcrumb={{ label: "Investigations", to: "/investigations" }}
        actions={
          <>
            <Link
              to={`/projects/${projectId}/incidents/explore`}
              className="inline-flex items-center justify-center rounded-md border border-graphite-600 bg-graphite-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:bg-graphite-700"
            >
              Open explorer
            </Link>
            <Button
              type="button"
              onClick={() => correlateMutation.mutate()}
              disabled={correlateMutation.isPending}
              aria-busy={correlateMutation.isPending}
            >
              {correlateMutation.isPending ? "Correlating…" : "Run correlation"}
            </Button>
          </>
        }
      />

      {correlateMutation.data ? (
        <Card>
          <CardHeader title="Last correlation" />
          <CardBody className="text-sm text-slate-300">
            {correlateMutation.data.message} · created {correlateMutation.data.incidents_created} · updated{" "}
            {correlateMutation.data.incidents_updated} · anomalies {correlateMutation.data.anomalies_processed}
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardBody className="py-4">
            <p className="text-[10px] uppercase text-slate-500">Total incidents</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-100">
              {incidentsQuery.data?.total ?? "—"}
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-4">
            <p className="text-[10px] uppercase text-slate-500">Critical</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-rose-200">
              {incidentsQuery.data?.severity_counts?.CRITICAL ?? 0}
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="py-4">
            <p className="text-[10px] uppercase text-slate-500">Open</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-sky-200">
              {incidentsQuery.data?.status_counts?.OPEN ?? 0}
            </p>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="By severity" />
          <CardBody className="h-56">
            {severityData.length === 0 ? (
              <p className="text-sm text-slate-500">No incidents yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3142" vertical={false} />
                  <XAxis dataKey="severity" stroke="#94a3b8" fontSize={11} />
                  <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#161a24", border: "1px solid #323a4d", borderRadius: 8 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="By status" />
          <CardBody className="h-56">
            {statusData.length === 0 ? (
              <p className="text-sm text-slate-500">No status data.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a3142" vertical={false} />
                  <XAxis dataKey="status" stroke="#94a3b8" fontSize={11} />
                  <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#161a24", border: "1px solid #323a4d", borderRadius: 8 }} />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Recent incidents" />
        <CardBody className="space-y-2">
          {incidentsQuery.data?.items.map((item) => (
            <Link
              key={item.id}
              to={`/projects/${projectId}/incidents/${item.id}`}
              className="flex flex-col gap-2 rounded-lg border border-graphite-700 px-3 py-3 transition-colors hover:border-graphite-600 hover:bg-graphite-850/40 sm:flex-row sm:items-center sm:justify-between"
            >
              <p className="text-sm font-medium text-slate-100">{item.title}</p>
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={item.severity} />
                <StatusBadge status={item.status} />
                <span className="text-xs text-slate-500">{formatRelative(item.last_activity_at)}</span>
              </div>
            </Link>
          ))}
          {(incidentsQuery.data?.items.length ?? 0) === 0 ? (
            <p className="text-sm text-slate-500">No incidents — run correlation after analysis.</p>
          ) : null}
        </CardBody>
      </Card>
    </div>
  );
}