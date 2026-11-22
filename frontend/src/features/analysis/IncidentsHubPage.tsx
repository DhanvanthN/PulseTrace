import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, Layers3 } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardBody } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { listProjects } from "@/services/projects";

export function IncidentsHubPage() {
  useDocumentTitle("Anomaly detection · PulseTrace");
  const projectsQuery = useQuery({
    queryKey: ["projects", "list"],
    queryFn: () => listProjects(),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-100">Anomaly detection</h1>
        <p className="text-sm text-slate-400">
          Run statistical and isolation-forest analysis on ingested logs, then explore anomalies and
          text-similarity clusters.
        </p>
      </section>

      {projectsQuery.isLoading ? (
        <Card>
          <CardBody className="h-24 animate-pulse bg-graphite-850/50">
            <span className="sr-only">Loading projects</span>
          </CardBody>
        </Card>
      ) : null}

      {projectsQuery.data?.total === 0 ? (
        <EmptyState
          icon={AlertTriangle}
          title="No projects available"
          description="Create a project and ingest logs before running analysis."
          footer={
            <Link className="text-sm text-accent-cyan hover:underline" to="/projects">
              Go to Projects
            </Link>
          }
        />
      ) : null}

      {projectsQuery.data && projectsQuery.data.items.length > 0 ? (
        <div className="space-y-3">
          {projectsQuery.data.items.map((project) => (
            <Card key={project.id}>
              <CardBody className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-slate-100">{project.name}</h2>
                  <p className="text-xs text-slate-500">{project.environment}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    to={`/projects/${project.id}/analysis`}
                    className="inline-flex items-center gap-1 rounded-md border border-graphite-600 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-graphite-800"
                  >
                    <BarChart3 className="h-3.5 w-3.5" aria-hidden />
                    Dashboard
                  </Link>
                  <Link
                    to={`/projects/${project.id}/anomalies`}
                    className="inline-flex items-center gap-1 rounded-md border border-indigo-500/30 bg-accent-indigo/15 px-2.5 py-1.5 text-xs text-accent-cyan hover:bg-accent-indigo/25"
                  >
                    <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
                    Anomalies
                  </Link>
                  <Link
                    to={`/projects/${project.id}/clusters`}
                    className="inline-flex items-center gap-1 rounded-md border border-graphite-600 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-graphite-800"
                  >
                    <Layers3 className="h-3.5 w-3.5" aria-hidden />
                    Clusters
                  </Link>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  );
}