import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, SearchCode } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardBody } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { listProjects } from "@/services/projects";

export function InvestigationsHubPage() {
  useDocumentTitle("Incidents · PulseTrace");
  const projectsQuery = useQuery({ queryKey: ["projects", "list"], queryFn: () => listProjects() });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="space-y-2">
        <h1 className="text-xl font-semibold text-slate-100">Incident intelligence</h1>
        <p className="text-sm text-slate-400">
          Correlate anomalies, clusters, logs and deployments into investigable incidents — correlation
          is not proof of causation.
        </p>
      </section>
      {projectsQuery.data?.items.map((project) => (
        <Card key={project.id}>
          <CardBody className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">{project.name}</h2>
              <p className="text-xs text-slate-500">{project.environment}</p>
            </div>
            <div className="flex gap-2">
              <Link
                to={`/projects/${project.id}/incidents`}
                className="inline-flex items-center gap-1 rounded-md border border-graphite-600 px-2.5 py-1.5 text-xs text-slate-200 hover:bg-graphite-800"
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                Dashboard
              </Link>
              <Link
                to={`/projects/${project.id}/incidents/explore`}
                className="inline-flex items-center gap-1 rounded-md border border-indigo-500/30 bg-accent-indigo/15 px-2.5 py-1.5 text-xs text-accent-cyan"
              >
                <SearchCode className="h-3.5 w-3.5" />
                Explorer
              </Link>
            </div>
          </CardBody>
        </Card>
      ))}
    </div>
  );
}