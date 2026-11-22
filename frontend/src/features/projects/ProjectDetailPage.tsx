import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { deleteProject, getProject, updateProject } from "@/services/projects";
import { AlertTriangle } from "lucide-react";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => getProject(projectId ?? ""),
    enabled: Boolean(projectId),
  });

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [environment, setEnvironment] = useState("development");
  const [formError, setFormError] = useState<string | null>(null);

  useDocumentTitle(
    projectQuery.data
      ? `${projectQuery.data.name} · PulseTrace`
      : "Project · PulseTrace"
  );

  useEffect(() => {
    if (projectQuery.data) {
      setName(projectQuery.data.name);
      setDescription(projectQuery.data.description ?? "");
      setEnvironment(projectQuery.data.environment);
    }
  }, [projectQuery.data]);

  const updateMutation = useMutation({
    mutationFn: () =>
      updateProject(projectId ?? "", {
        name: name.trim(),
        description: description.trim() ? description.trim() : null,
        environment,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteProject(projectId ?? ""),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      void navigate("/projects");
    },
  });

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await updateMutation.mutateAsync();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Update failed");
    }
  }

  if (projectQuery.isLoading) {
    return <div className="h-40 animate-pulse rounded-lg bg-graphite-900" />;
  }

  if (projectQuery.isError || !projectQuery.data) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Project not found"
        description="This project is unavailable or you may not have access."
        footer={
          <Link to="/projects" className="text-sm text-accent-cyan hover:underline">
            Back to projects
          </Link>
        }
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-xs text-slate-500">
            <Link to="/projects" className="hover:text-slate-300">
              Projects
            </Link>
          </p>
          <h1 className="text-xl font-semibold text-slate-100">{projectQuery.data.name}</h1>
        </div>
        <Button
          variant="danger"
          type="button"
          isLoading={deleteMutation.isPending}
          onClick={() => {
            if (window.confirm("Delete this project? This cannot be undone.")) {
              void deleteMutation.mutateAsync();
            }
          }}
        >
          Delete
        </Button>
      </div>

      <Card>
        <CardHeader title="Project settings" description="Update metadata and environment" />
        <CardBody>
          <form className="space-y-4" onSubmit={onSave}>
            <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <label className="block space-y-1.5">
              <span className="text-xs font-medium text-slate-400">Description</span>
              <textarea
                className="min-h-24 w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <label className="block space-y-1.5">
              <span className="text-xs font-medium text-slate-400">Environment</span>
              <select
                className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
                value={environment}
                onChange={(e) => setEnvironment(e.target.value)}
              >
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </label>
            {formError ? <p className="text-sm text-red-400">{formError}</p> : null}
            <Button type="submit" isLoading={updateMutation.isPending}>
              Save changes
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}