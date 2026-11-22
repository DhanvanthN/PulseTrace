import { useQueries, useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertOctagon,
  FolderKanban,
  Radar,
  Server,
  Siren,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "@/components/common/EmptyState";
import { MetricCard } from "@/components/common/MetricCard";
import { PageHeader } from "@/components/common/PageHeader";
import { SeverityBadge } from "@/components/incidents/SeverityBadge";
import { StatusBadge } from "@/components/incidents/StatusBadge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { listAnomalies } from "@/services/analysis";
import { listIncidents } from "@/services/incidents";
import { listProjects } from "@/services/projects";
import { listProjectServices } from "@/services/services";
import { formatRelative } from "@/utils/formatDate";
export function OverviewPage() {
  useDocumentTitle("Overview · PulseTrace");

  const projectsQuery = useQuery({
    queryKey: ["projects", "overview"],
    queryFn: () => listProjects(0, 50),
  });

  const projects = projectsQuery.data?.items ?? [];

  const incidentQueries = useQueries({
    queries: projects.map((project) => ({
      queryKey: ["incidents", project.id, "overview"],
      queryFn: () => listIncidents(project.id, { limit: 8 }),
      enabled: projects.length > 0,
    })),
  });

  const anomalyQueries = useQueries({
    queries: projects.map((project) => ({
      queryKey: ["anomalies", project.id, "overview"],
      queryFn: () => listAnomalies(project.id, { limit: 1 }),
      enabled: projects.length > 0,
    })),
  });

  const serviceQueries = useQueries({
    queries: projects.map((project) => ({
      queryKey: ["services", project.id, "overview"],
      queryFn: () => listProjectServices(project.id),
      enabled: projects.length > 0,
    })),
  });

  const loading =
    projectsQuery.isLoading ||
    incidentQueries.some((q) => q.isLoading) ||
    anomalyQueries.some((q) => q.isLoading);

  let totalIncidents = 0;
  let criticalIncidents = 0;
  let totalAnomalies = 0;
  let totalServices = 0;
  const severityTotals: Record<string, number> = {};
  const statusTotals: Record<string, number> = {};
  const recentIncidents: Array<{
    id: string;
    projectId: string;
    projectName: string;
    title: string;
    severity: string;
    status: string;
    last_activity_at: string;
  }> = [];

  incidentQueries.forEach((query, index) => {
    const data = query.data;
    if (!data) return;
    totalIncidents += data.total;
    const project = projects[index];
    Object.entries(data.severity_counts ?? {}).forEach(([sev, count]) => {
      severityTotals[sev] = (severityTotals[sev] ?? 0) + count;
      if (sev === "CRITICAL") criticalIncidents += count;
    });
    Object.entries(data.status_counts ?? {}).forEach(([st, count]) => {
      statusTotals[st] = (statusTotals[st] ?? 0) + count;
    });
    data.items.forEach((item) => {
      if (!project) return;
      recentIncidents.push({
        id: item.id,
        projectId: project.id,
        projectName: project.name,
        title: item.title,
        severity: item.severity,
        status: item.status,
        last_activity_at: item.last_activity_at,
      });
    });
  });

  anomalyQueries.forEach((query) => {
    totalAnomalies += query.data?.total ?? 0;
  });

  serviceQueries.forEach((query) => {
    totalServices += query.data?.items.length ?? 0;
  });

  recentIncidents.sort(
    (a, b) => new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime()
  );

  const severityColors: Record<string, string> = {
    CRITICAL: "#f43f5e",
    HIGH: "#f97316",
    MEDIUM: "#f59e0b",
    LOW: "#64748b",
  };
  const severityChart = Object.entries(severityTotals).map(([severity, count]) => ({
    severity,
    count,
    fill: severityColors[severity] ?? "#6366f1",
  }));

  const statusChart = Object.entries(statusTotals).map(([status, count]) => ({ status, count }));

  const hasProjects = projects.length > 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Overview"
        description="Live summary across your projects — metrics reflect API data only."
      />

      <section aria-label="Summary metrics" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Projects" icon={FolderKanban} value={hasProjects ? projects.length : null} loading={loading} />
        <MetricCard
          label="Open incidents"
          icon={Siren}
          value={hasProjects ? totalIncidents : null}
          hint={hasProjects ? `${criticalIncidents} critical` : undefined}
          loading={loading}
        />
        <MetricCard
          label="Registered services"
          icon={Server}
          value={hasProjects ? totalServices : null}
          loading={loading}
        />
        <MetricCard
          label="Detected anomalies"
          icon={Radar}
          value={hasProjects ? totalAnomalies : null}
          loading={loading}
        />
      </section>

      {!hasProjects && !projectsQuery.isLoading ? (
        <EmptyState
          data-testid="overview-empty-dashboard"
          icon={Activity}
          title="No projects yet"
          description="Create a project to ingest logs, run analysis, and investigate incidents."
          footer={
            <Link
              to="/projects"
              className="text-sm text-accent-cyan hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-indigo/50 rounded"
            >
              Go to projects
            </Link>
          }
        />
      ) : null}

      {hasProjects ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Incidents by severity" description="Aggregated across projects" />
            <CardBody className="h-56">
              {severityChart.length === 0 ? (
                <p className="text-sm text-slate-500">No incidents recorded yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={severityChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3142" vertical={false} />
                    <XAxis dataKey="severity" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <Tooltip
                      cursor={{ fill: "rgba(99,102,241,0.08)" }}
                      contentStyle={{
                        background: "#161a24",
                        border: "1px solid #323a4d",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Incidents by status" />
            <CardBody className="h-56">
              {statusChart.length === 0 ? (
                <p className="text-sm text-slate-500">No status breakdown available.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3142" vertical={false} />
                    <XAxis dataKey="status" stroke="#94a3b8" fontSize={10} tickLine={false} />
                    <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "#161a24",
                        border: "1px solid #323a4d",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardBody>
          </Card>
        </div>
      ) : null}

      {hasProjects ? (
        <Card>
          <CardHeader title="Recent incidents" description="Latest activity across projects" />
          <CardBody className="space-y-2">
            {recentIncidents.length === 0 ? (
              <EmptyState
                icon={AlertOctagon}
                title="No incidents"
                description="Run correlation on a project after analysis detects anomalies."
                className="py-6"
              />
            ) : (
              recentIncidents.slice(0, 8).map((item) => (
                <Link
                  key={`${item.projectId}-${item.id}`}
                  to={`/projects/${item.projectId}/incidents/${item.id}`}
                  className="flex flex-col gap-2 rounded-lg border border-graphite-700 px-3 py-3 transition-colors hover:border-graphite-600 hover:bg-graphite-850/40 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-100">{item.title}</p>
                    <p className="text-xs text-slate-500">{item.projectName}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={item.severity} />
                    <StatusBadge status={item.status} />
                    <span className="text-xs text-slate-500">{formatRelative(item.last_activity_at)}</span>
                  </div>
                </Link>
              ))
            )}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}