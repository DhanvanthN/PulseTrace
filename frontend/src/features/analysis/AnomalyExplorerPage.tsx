import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { getAnomaly, listAnomalies } from "@/services/analysis";
import { listProjectServices } from "@/services/services";
import { AlertTriangle } from "lucide-react";

const SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

export function AnomalyExplorerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams] = useSearchParams();
  useDocumentTitle("Anomaly explorer · PulseTrace");

  const [severity, setSeverity] = useState("");
  const [anomalyType, setAnomalyType] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [page, setPage] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get("selected"));
  const limit = 20;

  const filters = useMemo(
    () => ({
      severity: severity || undefined,
      anomaly_type: anomalyType || undefined,
      service_id: serviceId || undefined,
      skip: page * limit,
      limit,
    }),
    [anomalyType, page, serviceId, severity]
  );

  const anomaliesQuery = useQuery({
    queryKey: ["anomalies", projectId, filters],
    queryFn: () => listAnomalies(projectId ?? "", filters),
    enabled: Boolean(projectId),
  });

  const servicesQuery = useQuery({
    queryKey: ["services", projectId],
    queryFn: () => listProjectServices(projectId ?? ""),
    enabled: Boolean(projectId),
  });

  const detailQuery = useQuery({
    queryKey: ["anomaly-detail", projectId, selectedId],
    queryFn: () => getAnomaly(projectId ?? "", selectedId ?? ""),
    enabled: Boolean(projectId && selectedId),
  });

  const total = anomaliesQuery.data?.total ?? 0;
  const maxPage = Math.max(0, Math.ceil(total / limit) - 1);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <p className="text-xs text-slate-500">
          <Link to={`/projects/${projectId}/analysis`} className="hover:text-slate-300">
            Analysis
          </Link>
        </p>
        <h1 className="text-xl font-semibold text-slate-100">Anomaly explorer</h1>
      </div>

      <Card>
        <CardHeader title="Filters" />
        <CardBody className="grid gap-3 md:grid-cols-3">
          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-slate-400">Severity</span>
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
              value={severity}
              onChange={(event) => {
                setSeverity(event.target.value);
                setPage(0);
              }}
            >
              <option value="">All</option>
              {SEVERITIES.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </label>
          <Input
            label="Anomaly type"
            value={anomalyType}
            onChange={(event) => {
              setAnomalyType(event.target.value);
              setPage(0);
            }}
          />
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
              <option value="">All</option>
              {servicesQuery.data?.items.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>
          </label>
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title={`Results (${total})`} />
          <CardBody className="space-y-2">
            {anomaliesQuery.isLoading ? <p className="text-sm text-slate-500">Loading…</p> : null}
            {anomaliesQuery.isError ? (
              <p className="text-sm text-red-400">Failed to load anomalies.</p>
            ) : null}
            {anomaliesQuery.data?.total === 0 ? (
              <EmptyState
                icon={AlertTriangle}
                title="No anomalies"
                description="Run analysis from the dashboard after logs are ingested."
              />
            ) : null}
            {anomaliesQuery.data?.items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                  selectedId === item.id
                    ? "border-accent-cyan/50 bg-accent-indigo/10"
                    : "border-graphite-700 hover:bg-graphite-850/50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-slate-100">{item.anomaly_type}</span>
                  <Badge variant={item.severity === "CRITICAL" ? "accent" : "default"}>{item.severity}</Badge>
                </div>
                <p className="text-xs text-slate-500">{item.description}</p>
              </button>
            ))}
            {total > limit ? (
              <div className="flex items-center justify-between pt-2 text-xs text-slate-400">
                <button
                  type="button"
                  disabled={page === 0}
                  className="disabled:opacity-40"
                  onClick={() => setPage((value) => Math.max(0, value - 1))}
                >
                  Previous
                </button>
                <span>
                  Page {page + 1} / {maxPage + 1}
                </span>
                <button
                  type="button"
                  disabled={page >= maxPage}
                  className="disabled:opacity-40"
                  onClick={() => setPage((value) => Math.min(maxPage, value + 1))}
                >
                  Next
                </button>
              </div>
            ) : null}
          </CardBody>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader title="Evidence" />
          <CardBody className="space-y-3 text-sm text-slate-300">
            {!selectedId ? <p className="text-slate-500">Select an anomaly to inspect evidence.</p> : null}
            {detailQuery.isLoading ? <p className="text-slate-500">Loading detail…</p> : null}
            {detailQuery.data ? (
              <>
                <p className="text-slate-100">{detailQuery.data.description}</p>
                <p>
                  Method: <span className="text-slate-100">{detailQuery.data.detection_method}</span>
                </p>
                <p>
                  Score: {detailQuery.data.score.toFixed(3)}{" "}
                  <span className="text-xs text-slate-500">(not a calibrated probability)</span>
                </p>
                <pre className="max-h-96 overflow-auto rounded-md border border-graphite-700 bg-graphite-900 p-3 text-xs text-slate-300">
                  {JSON.stringify(detailQuery.data.evidence, null, 2)}
                </pre>
              </>
            ) : null}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}