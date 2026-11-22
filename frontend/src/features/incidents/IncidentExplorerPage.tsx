import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Plus, Siren } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { SeverityBadge } from "@/components/incidents/SeverityBadge";
import { StatusBadge } from "@/components/incidents/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { createIncident, listIncidents } from "@/services/incidents";
import { formatDateTime, formatRelative } from "@/utils/formatDate";
const STATUSES = ["OPEN", "INVESTIGATING", "RESOLVED", "IGNORED"] as const;
const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

export function IncidentExplorerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Incident explorer · PulseTrace");
  const queryClient = useQueryClient();

  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [title, setTitle] = useState("");
  const limit = 20;

  const filters = useMemo(
    () => ({
      status: status || undefined,
      severity: severity || undefined,
      search: search || undefined,
      skip: page * limit,
      limit,
    }),
    [page, search, severity, status]
  );

  const incidentsQuery = useQuery({
    queryKey: ["incidents", projectId, filters],
    queryFn: () => listIncidents(projectId ?? "", filters),
    enabled: Boolean(projectId),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createIncident(projectId ?? "", { title, description: "Manual incident", severity: "MEDIUM" }),
    onSuccess: () => {
      setTitle("");
      queryClient.invalidateQueries({ queryKey: ["incidents", projectId] });
    },
  });

  const total = incidentsQuery.data?.total ?? 0;
  const maxPage = Math.max(0, Math.ceil(total / limit) - 1);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Incident explorer"
        description="Search correlated and manual incidents for this project."
        breadcrumb={{ label: "Incident dashboard", to: `/projects/${projectId}/incidents` }}
      />

      <Card>
        <CardHeader title="Create incident" description="Manual incidents for tracking outside correlation." />
        <CardBody className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="min-w-[240px] flex-1"
          />
          <Button
            type="button"
            disabled={!title.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            <Plus className="mr-2 h-4 w-4" aria-hidden />
            Create
          </Button>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Filters" />
        <CardBody className="grid gap-3 md:grid-cols-3">
          <Input
            label="Search title"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
          />
          <label className="block space-y-1.5 text-xs text-slate-400">
            Status
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200 transition-colors hover:border-graphite-600 focus:border-accent-indigo/50"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All statuses</option>
              {STATUSES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5 text-xs text-slate-400">
            Severity
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200 transition-colors hover:border-graphite-600 focus:border-accent-indigo/50"
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All severities</option>
              {SEVERITIES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title={`Incidents (${total})`} />
        <CardBody>
          {incidentsQuery.isLoading ? (
            <p className="text-sm text-slate-500" aria-live="polite">
              Loading incidents…
            </p>
          ) : null}
          {incidentsQuery.isError ? (
            <p className="text-sm text-rose-300/90" role="alert">
              Could not load incidents.
            </p>
          ) : null}
          {!incidentsQuery.isLoading && total === 0 ? (
            <EmptyState
              icon={Siren}
              title="No incidents"
              description="Run correlation from the incident dashboard or create a manual incident."
            />
          ) : null}

          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-graphite-700 text-[10px] uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2 font-medium">Title</th>
                  <th className="px-2 py-2 font-medium">Severity</th>
                  <th className="px-2 py-2 font-medium">Status</th>
                  <th className="px-2 py-2 font-medium">Last activity</th>
                </tr>
              </thead>
              <tbody>
                {incidentsQuery.data?.items.map((item) => (
                  <tr key={item.id} className="border-b border-graphite-800/80 transition-colors hover:bg-graphite-850/40">
                    <td className="px-2 py-3">
                      <Link
                        data-testid="incident-table-link"
                        to={`/projects/${projectId}/incidents/${item.id}`}
                        className="font-medium text-slate-100 hover:text-accent-cyan focus-visible:outline-none focus-visible:underline"
                      >
                        {item.title}
                      </Link>
                      {item.description ? (
                        <p className="mt-0.5 line-clamp-1 text-xs text-slate-500">{item.description}</p>
                      ) : null}
                    </td>
                    <td className="px-2 py-3">
                      <SeverityBadge severity={item.severity} />
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-2 py-3 text-xs text-slate-400">
                      <span title={formatDateTime(item.last_activity_at)}>{formatRelative(item.last_activity_at)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-2 md:hidden">
            {incidentsQuery.data?.items.map((item) => (
              <Link
                key={item.id}
                to={`/projects/${projectId}/incidents/${item.id}`}
                className="block rounded-lg border border-graphite-700 px-3 py-3 transition-colors hover:border-graphite-600 hover:bg-graphite-850/40"
              >
                <p className="font-medium text-slate-100">{item.title}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <SeverityBadge severity={item.severity} />
                  <StatusBadge status={item.status} />
                </div>
                <p className="mt-2 text-xs text-slate-500">{formatRelative(item.last_activity_at)}</p>
              </Link>
            ))}
          </div>

          {total > limit ? (
            <nav
              className="mt-4 flex items-center justify-between border-t border-graphite-800 pt-3 text-xs text-slate-400"
              aria-label="Incident pagination"
            >
              <Button
                type="button"
                variant="secondary"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                <ChevronLeft className="h-4 w-4" aria-hidden />
                Previous
              </Button>
              <span>
                Page {page + 1} of {maxPage + 1}
              </span>
              <Button
                type="button"
                variant="secondary"
                disabled={page >= maxPage}
                onClick={() => setPage((p) => Math.min(maxPage, p + 1))}
              >
                Next
                <ChevronRight className="h-4 w-4" aria-hidden />
              </Button>
            </nav>
          ) : null}
        </CardBody>
      </Card>
    </div>
  );
}