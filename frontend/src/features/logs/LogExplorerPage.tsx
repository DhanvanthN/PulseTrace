import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { getLog, searchLogs } from "@/services/logs";
import { listProjectServices } from "@/services/services";
import type { LogEntry } from "@/types/log";
import { FileSearch } from "lucide-react";

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] as const;

export function LogExplorerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Log search · PulseTrace");

  const [keyword, setKeyword] = useState("");
  const [level, setLevel] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [traceId, setTraceId] = useState("");
  const [page, setPage] = useState(0);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const limit = 25;

  const filters = useMemo(
    () => ({
      keyword: keyword || undefined,
      level: level || undefined,
      service_id: serviceId || undefined,
      trace_id: traceId || undefined,
      skip: page * limit,
      limit,
    }),
    [keyword, level, page, serviceId, traceId]
  );

  const logsQuery = useQuery({
    queryKey: ["logs", projectId, filters],
    queryFn: () => searchLogs(projectId ?? "", filters),
    enabled: Boolean(projectId),
  });

  const servicesQuery = useQuery({
    queryKey: ["services", projectId],
    queryFn: () => listProjectServices(projectId ?? ""),
    enabled: Boolean(projectId),
  });

  const detailQuery = useQuery({
    queryKey: ["log-detail", projectId, selectedLogId],
    queryFn: () => getLog(projectId ?? "", selectedLogId ?? ""),
    enabled: Boolean(projectId && selectedLogId),
  });

  const total = logsQuery.data?.total ?? 0;
  const maxPage = Math.max(0, Math.ceil(total / limit) - 1);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs text-slate-500">
            <Link to="/logs" className="hover:text-slate-300">
              Log Explorer
            </Link>
          </p>
          <h1 className="text-xl font-semibold text-slate-100">Search logs</h1>
        </div>
        <Link to={`/projects/${projectId}/logs/upload`}>
          <Button type="button" variant="secondary">
            Upload logs
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader title="Filters" />
        <CardBody className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Input
            label="Keyword"
            value={keyword}
            onChange={(event) => {
              setKeyword(event.target.value);
              setPage(0);
            }}
          />
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-slate-400">Level</span>
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
              value={level}
              onChange={(event) => {
                setLevel(event.target.value);
                setPage(0);
              }}
            >
              <option value="">All levels</option>
              {LEVELS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-slate-400">Service</span>
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
              value={serviceId}
              onChange={(event) => {
                setServiceId(event.target.value);
                setPage(0);
              }}
            >
              <option value="">All services</option>
              {servicesQuery.data?.items.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Trace ID"
            value={traceId}
            onChange={(event) => {
              setTraceId(event.target.value);
              setPage(0);
            }}
          />
          <Button
            type="button"
            variant="ghost"
            className="md:col-span-2 xl:col-span-4"
            onClick={() => {
              setKeyword("");
              setLevel("");
              setServiceId("");
              setTraceId("");
              setPage(0);
            }}
          >
            Clear filters
          </Button>
        </CardBody>
      </Card>

      {logsQuery.isLoading ? (
        <Card>
          <CardBody className="h-48 animate-pulse bg-graphite-850/40">
            <span className="sr-only">Loading logs</span>
          </CardBody>
        </Card>
      ) : null}

      {logsQuery.isError ? (
        <EmptyState
          icon={FileSearch}
          title="Unable to load logs"
          description="Check your filters and try again."
        />
      ) : null}

      {logsQuery.data && logsQuery.data.total === 0 ? (
        <EmptyState
          data-testid="logs-empty-state"
          icon={FileSearch}
          title="No logs found"
          description="Upload a log batch to begin exploring records for this project."
          footer={
            <Link
              to={`/projects/${projectId}/logs/upload`}
              className="text-sm text-accent-cyan hover:underline"
            >
              Upload logs
            </Link>
          }
        />
      ) : null}

      {logsQuery.data && logsQuery.data.items.length > 0 ? (
        <Card>
          <CardHeader title={`Results (${total})`} description="Sorted by newest timestamp" />
          <CardBody className="space-y-2 p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-graphite-700 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-2">Timestamp</th>
                    <th className="px-4 py-2">Level</th>
                    <th className="px-4 py-2">Service</th>
                    <th className="px-4 py-2">Message</th>
                    <th className="px-4 py-2 text-right"> </th>
                  </tr>
                </thead>
                <tbody>
                  {logsQuery.data.items.map((entry) => (
                    <tr
                      key={entry.id}
                      data-testid="log-row"
                      data-log-id={entry.id}
                      className="cursor-pointer border-b border-graphite-800/80 hover:bg-graphite-850/40"
                      onClick={() => setSelectedLogId(entry.id)}
                    >
                      <td className="px-4 py-2 text-xs text-slate-400">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-2">
                        <Badge>{entry.level}</Badge>
                      </td>
                      <td className="px-4 py-2 text-slate-300">
                        {entry.service_name ?? "—"}
                      </td>
                      <td className="max-w-xl truncate px-4 py-2 text-slate-200">
                        {entry.message}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <Button
                          type="button"
                          variant="ghost"
                          className="text-xs"
                          data-testid="log-row-view"
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelectedLogId(entry.id);
                          }}
                        >
                          View
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <LinkBar page={page} maxPage={maxPage} onPageChange={setPage} />
          </CardBody>
        </Card>
      ) : null}

      {selectedLogId ? (
        detailQuery.isLoading ? (
          <Card data-testid="log-detail-loading">
            <CardBody className="text-sm text-slate-500">Loading log details…</CardBody>
          </Card>
        ) : detailQuery.isError ? (
          <p className="text-sm text-red-400" role="alert" data-testid="log-detail-error">
            Unable to load log details.
          </p>
        ) : detailQuery.data ? (
          <LogDetailPanel log={detailQuery.data} onClose={() => setSelectedLogId(null)} />
        ) : null
      ) : null}
    </div>
  );
}

function LinkBar({
  page,
  maxPage,
  onPageChange,
}: {
  page: number;
  maxPage: number;
  onPageChange: (page: number) => void;
}) {
  return (
    <div className="flex items-center justify-between border-t border-graphite-700 px-4 py-3">
      <span className="text-xs text-slate-500">
        Page {page + 1} of {maxPage + 1}
      </span>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="secondary"
          disabled={page <= 0}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={page >= maxPage}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

function LogDetailPanel({ log, onClose }: { log: LogEntry; onClose: () => void }) {
  return (
    <Card data-testid="log-detail-panel">
      <CardHeader
        title="Log details"
        action={
          <Button type="button" variant="ghost" onClick={onClose}>
            Close
          </Button>
        }
      />
      <CardBody className="grid gap-2 text-sm md:grid-cols-2">
        <DetailField label="Timestamp" value={new Date(log.timestamp).toISOString()} />
        <DetailField label="Severity" value={log.level} />
        <DetailField label="Service" value={log.service_name ?? "—"} />
        <DetailField label="Trace ID" value={log.trace_id ?? "—"} />
        <DetailField label="Request ID" value={log.request_id ?? "—"} />
        <DetailField label="Batch ID" value={log.batch_id} />
        <DetailField label="Fingerprint" value={log.fingerprint} className="md:col-span-2" />
        <DetailField label="Message" value={log.message} className="md:col-span-2" />
        <DetailField
          label="Metadata"
          value={JSON.stringify(log.metadata, null, 2)}
          className="md:col-span-2"
        />
      </CardBody>
    </Card>
  );
}

function DetailField({
  label,
  value,
  className = "",
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 break-words font-mono text-xs text-slate-200">{value}</p>
    </div>
  );
}