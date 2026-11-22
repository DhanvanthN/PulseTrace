import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";

interface CreateProjectDialogProps {
  onClose: () => void;
  onCreate: (payload: {
    name: string;
    description?: string | null;
    environment: string;
  }) => Promise<void>;
  isSubmitting: boolean;
}

export function CreateProjectDialog({
  onClose,
  onCreate,
  isSubmitting,
}: CreateProjectDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [environment, setEnvironment] = useState("development");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await onCreate({
        name: name.trim(),
        description: description.trim() ? description.trim() : null,
        environment,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader
          title="Create project"
          description="Organize services, incidents and telemetry by project"
          action={
            <Button variant="ghost" type="button" onClick={onClose}>
              Close
            </Button>
          }
        />
        <CardBody>
          <form className="space-y-4" onSubmit={onSubmit}>
            <Input label="Name" name="name" required value={name} onChange={(e) => setName(e.target.value)} />
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
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button type="submit" isLoading={isSubmitting}>
              Create project
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}