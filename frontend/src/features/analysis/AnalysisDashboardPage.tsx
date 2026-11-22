import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { listAnomalies, runAnalysis } from "@/services/analysis";

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "#64748b",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export function AnalysisDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Analysis dashboard · PulseTrace");
  const queryClient = useQueryClient();

  const anomaliesQuery = useQuery({
    queryKey: ["anomalies", projectId, { skip: 0, limit: 8 }],
    queryFn: () => listAnomalies(projectId ?? "", { skip: 0, limit: 8 }),
    enabled: Boolean(projectId),
  });

  const runMutation = useMutation({
    mutationFn: () => runAnalysis(projectId ?? ""),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["anomalies", projectId] });
      queryClient.invalidateQueries({ queryKey: ["clusters", projectId] });
    },
  });

  const severityData = Object.entries(anomaliesQuery.data?.severity_counts ?? {}).map(([severity, count]) => ({
    severity,
    count,
    fill: SEVERITY_COLORS[severity] ?? "#94a3b8",
  }));

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs text-slate-500">
            <Link to="/incidents" className="hover:text-slate-300">
              Anomaly detection
            </Link>
          </p>
          <h1 className="text-xl font-semibold text-slate-100">Analysis dashboard</h1>
        </div>
        <div className="flex gap-2">
          <Link to={`/projects/${projectId}/anomalies`}>
            <Button type="button" variant="secondary">
              View anomalies
            </Button>
          </Link>
          <Button
            type="button"
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
          >
            {runMutation.isPending ? "Running…" : "Run analysis"}
          </Button>
        </div>
      </div>

      {runMutation.data ? (
        <Card>
          <CardHeader title="Last run" />
          <CardBody className="grid gap-2 text-sm text-slate-300 md:grid-cols-2">
            <p>
              Status: <span className="text-slate-100">{runMutation.data.status}</span> —{" "}
              {runMutation.data.message}
            </p>
            <p>Logs analyzed: {runMutation.data.logs_analyzed}</p>
            <p>
              Anomalies detected: {runMutation.data.anomalies_detected} (new: {runMutation.data.anomalies_created})
            </p>
            <p>
              Clusters: {runMutation.data.clusters_created} · memberships {runMutation.data.cluster_memberships} ·
              noise {runMutation.data.noise_logs}
            </p>
            <p className="md:col-span-2 text-xs text-slate-500">
              Methods: {runMutation.data.methods.join(", ")} · window{" "}
              {runMutation.data.window_start ?? "—"} → {runMutation.data.window_end ?? "—"}
            </p>
          </CardBody>
        </Card>
      ) : null}

      {runMutation.isError ? (
        <p className="text-sm text-red-400">Analysis request failed. Check backend logs and try again.</p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Severity distribution" />
          <CardBody className="h-64">
            {anomaliesQuery.isLoading ? (
              <p className="text-sm text-slate-500">Loading…</p>
            ) : severityData.length === 0 ? (
              <p className="text-sm text-slate-500">No anomalies yet. Run analysis after ingesting logs.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="severity" stroke="#94a3b8" fontSize={12} />
                  <YAxis allowDecimals={false} stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 12 }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Recent anomalies" />
          <CardBody className="space-y-2">
            {anomaliesQuery.data?.items.length === 0 ? (
              <p className="text-sm text-slate-500">No anomalies to display.</p>
            ) : (
              anomaliesQuery.data?.items.map((item) => (
                <Link
                  key={item.id}
                  to={`/projects/${projectId}/anomalies?selected=${item.id}`}
                  className="block rounded-md border border-graphite-700/80 px-3 py-2 hover:bg-graphite-850/60"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm text-slate-100">{item.description}</span>
                    <Badge variant={item.severity === "CRITICAL" ? "accent" : "default"}>{item.severity}</Badge>
                  </div>
                  <p className="text-xs text-slate-500">{item.anomaly_type}</p>
                </Link>
              ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}