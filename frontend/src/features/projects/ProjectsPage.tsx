import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderKanban, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { createProject, listProjects } from "@/services/projects";

export function ProjectsPage() {
  useDocumentTitle("Projects · PulseTrace");
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  const projectsQuery = useQuery({
    queryKey: ["projects", "list"],
    queryFn: () => listProjects(),
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Projects</h1>
          <p className="text-sm text-slate-400">
            Manage observability workspaces and ownership boundaries.
          </p>
        </div>
        <Button type="button" onClick={() => setShowCreate(true)}>
          <span className="inline-flex items-center gap-1.5">
            <Plus className="h-4 w-4" aria-hidden />
            New project
          </span>
        </Button>
      </div>

      {projectsQuery.isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {[1, 2].map((item) => (
            <Card key={item}>
              <CardBody className="h-28 animate-pulse bg-graphite-850/40">
                <span className="sr-only">Loading</span>
              </CardBody>
            </Card>
          ))}
        </div>
      ) : null}

      {projectsQuery.isError ? (
        <EmptyState
          icon={FolderKanban}
          title="Unable to load projects"
          description="Check your connection and try again."
        />
      ) : null}

      {projectsQuery.data && projectsQuery.data.total === 0 ? (
        <EmptyState
          data-testid="projects-empty-state"
          icon={FolderKanban}
          title="No projects yet"
          description="Create your first project to organize services and incident workflows."
          footer={
            <Button type="button" onClick={() => setShowCreate(true)}>
              Create project
            </Button>
          }
        />
      ) : null}

      {projectsQuery.data && projectsQuery.data.items.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {projectsQuery.data.items.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="transition-colors hover:border-graphite-600">
                <CardBody className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h2 className="text-sm font-semibold text-slate-100">{project.name}</h2>
                    <Badge variant="accent">{project.environment}</Badge>
                  </div>
                  <p className="line-clamp-2 text-xs text-slate-500">
                    {project.description ?? "No description"}
                  </p>
                </CardBody>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}

      {showCreate ? (
        <CreateProjectDialog
          onClose={() => setShowCreate(false)}
          isSubmitting={createMutation.isPending}
          onCreate={async (payload) => {
            await createMutation.mutateAsync(payload);
          }}
        />
      ) : null}
    </div>
  );
}