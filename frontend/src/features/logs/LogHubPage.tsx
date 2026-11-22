import { useQuery } from "@tanstack/react-query";
import { FileSearch, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardBody } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { listProjects } from "@/services/projects";

export function LogHubPage() {
  useDocumentTitle("Log Explorer · PulseTrace");
  const projectsQuery = useQuery({
    queryKey: ["projects", "list"],
    queryFn: () => listProjects(),
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-100">Log Explorer</h1>
        <p className="text-sm text-slate-400">
          Select a project to search ingested logs or upload a new batch.
        </p>
      </section>

      {projectsQuery.isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((key) => (
            <Card key={key}>
              <CardBody className="h-20 animate-pulse bg-graphite-850/50">
                <span className="sr-only">Loading</span>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : null}

      {projectsQuery.data?.total === 0 ? (
        <EmptyState
          icon={FileSearch}
          title="No projects available"
          description="Create a project before ingesting or exploring logs."
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
                <div className="flex items-center gap-2">
                  <Link
                    to={`/projects/${project.id}/logs`}
                    className="inline-flex items-center gap-1 rounded-md border border-graphite-600 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-graphite-800"
                  >
                    <FileSearch className="h-3.5 w-3.5" aria-hidden />
                    Explore
                  </Link>
                  <Link
                    to={`/projects/${project.id}/logs/upload`}
                    className="inline-flex items-center gap-1 rounded-md border border-indigo-500/30 bg-accent-indigo/15 px-2.5 py-1.5 text-xs text-accent-cyan hover:bg-accent-indigo/25"
                  >
                    <Upload className="h-3.5 w-3.5" aria-hidden />
                    Upload
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