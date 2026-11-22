import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { getCluster, listClusters } from "@/services/analysis";
import { Layers3 } from "lucide-react";

export function ClusterExplorerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Log clusters · PulseTrace");

  const [search, setSearch] = useState("");
  const [minLogCount, setMinLogCount] = useState(2);
  const [page, setPage] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const limit = 15;

  const filters = useMemo(
    () => ({
      search: search || undefined,
      min_log_count: minLogCount,
      skip: page * limit,
      limit,
    }),
    [minLogCount, page, search]
  );

  const clustersQuery = useQuery({
    queryKey: ["clusters", projectId, filters],
    queryFn: () => listClusters(projectId ?? "", filters),
    enabled: Boolean(projectId),
  });

  const detailQuery = useQuery({
    queryKey: ["cluster-detail", projectId, selectedId],
    queryFn: () => getCluster(projectId ?? "", selectedId ?? ""),
    enabled: Boolean(projectId && selectedId),
  });

  const total = clustersQuery.data?.total ?? 0;
  const maxPage = Math.max(0, Math.ceil(total / limit) - 1);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div>
        <p className="text-xs text-slate-500">
          <Link to={`/projects/${projectId}/analysis`} className="hover:text-slate-300">
            Analysis
          </Link>
        </p>
        <h1 className="text-xl font-semibold text-slate-100">Log clustering</h1>
        <p className="text-xs text-slate-500">
          TF-IDF + DBSCAN text similarity (not semantic understanding).
        </p>
      </div>

      <Card>
        <CardHeader title="Filters" />
        <CardBody className="grid gap-3 md:grid-cols-2">
          <Input
            label="Search representative message"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(0);
            }}
          />
          <Input
            label="Minimum log count"
            type="number"
            value={String(minLogCount)}
            onChange={(event) => {
              setMinLogCount(Math.max(1, Number(event.target.value) || 1));
              setPage(0);
            }}
          />
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title={`Clusters (${total})`} />
          <CardBody className="space-y-2">
            {clustersQuery.isLoading ? <p className="text-sm text-slate-500">Loading…</p> : null}
            {clustersQuery.data?.total === 0 ? (
              <EmptyState
                icon={Layers3}
                title="No clusters"
                description="Run analysis to build text-similarity clusters from recent logs."
              />
            ) : null}
            {clustersQuery.data?.items.map((item) => (
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
                <p className="font-medium text-slate-100">{item.cluster_label}</p>
                <p className="line-clamp-2 text-xs text-slate-500">{item.representative_message}</p>
                <p className="text-xs text-slate-400">{item.log_count} logs</p>
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
          <CardHeader title="Cluster detail" />
          <CardBody className="space-y-3 text-sm text-slate-300">
            {!selectedId ? <p className="text-slate-500">Select a cluster to view member logs.</p> : null}
            {detailQuery.data ? (
              <>
                <p className="text-slate-100">{detailQuery.data.description}</p>
                <p className="rounded-md border border-graphite-700 bg-graphite-900 px-3 py-2 text-xs text-slate-200">
                  {detailQuery.data.representative_message}
                </p>
                <p>
                  {detailQuery.data.log_count} logs · {detailQuery.data.first_seen ?? "—"} →{" "}
                  {detailQuery.data.last_seen ?? "—"}
                </p>
                <ul className="max-h-80 space-y-2 overflow-auto text-xs">
                  {detailQuery.data.logs.map((log) => (
                    <li key={log.id} className="rounded border border-graphite-800 px-2 py-1.5">
                      <span className="text-slate-500">{log.timestamp}</span>{" "}
                      <span className="text-amber-300">{log.level}</span> {log.message}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}