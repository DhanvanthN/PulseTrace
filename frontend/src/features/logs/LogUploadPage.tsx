import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { uploadLogs } from "@/services/logs";
import { listProjectServices } from "@/services/services";
import type { LogBatch } from "@/types/log";

const ACCEPTED = ".csv,.json,.jsonl,.txt";

export function LogUploadPage() {
  const { projectId } = useParams<{ projectId: string }>();
  useDocumentTitle("Log Ingestion · PulseTrace");

  const [file, setFile] = useState<File | null>(null);
  const [serviceId, setServiceId] = useState("");
  const [result, setResult] = useState<LogBatch | null>(null);
  const [error, setError] = useState<string | null>(null);

  const servicesQuery = useQuery({
    queryKey: ["services", projectId],
    queryFn: () => listProjectServices(projectId ?? ""),
    enabled: Boolean(projectId),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!projectId || !file) {
        throw new Error("Select a file to upload");
      }
      return uploadLogs(projectId, file, serviceId || undefined);
    },
    onSuccess: (batch) => {
      setResult(batch);
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Upload failed");
    },
  });

  function onFileSelected(selected: File | null) {
    setFile(selected);
    setError(null);
    setResult(null);
    if (selected) {
      const extension = selected.name.slice(selected.name.lastIndexOf(".")).toLowerCase();
      const allowed = ACCEPTED.split(",");
      if (!allowed.includes(extension)) {
        setError(`Unsupported format. Accepted: ${ACCEPTED}`);
        setFile(null);
      }
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <p className="text-xs text-slate-500">
          <Link to="/logs" className="hover:text-slate-300">
            Log Explorer
          </Link>
        </p>
        <h1 className="text-xl font-semibold text-slate-100">Log ingestion</h1>
      </div>

      <Card>
        <CardHeader
          title="Upload log file"
          description={`Supported formats: CSV, JSON, JSONL, TXT (${ACCEPTED})`}
        />
        <CardBody className="space-y-4">
          <label
            data-testid="log-upload-dropzone"
            className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-graphite-600 bg-graphite-850/30 p-6 text-center"
          >
            <input
              type="file"
              accept={ACCEPTED}
              className="hidden"
              onChange={(event) => onFileSelected(event.target.files?.[0] ?? null)}
            />
            <p className="text-sm text-slate-300">
              {file ? file.name : "Drag & drop or click to select a file"}
            </p>
            {file ? <p className="mt-1 text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p> : null}
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-slate-400">
              Optional service override
            </span>
            <select
              className="w-full rounded-md border border-graphite-700 bg-graphite-850 px-3 py-2 text-sm text-slate-200"
              value={serviceId}
              onChange={(event) => setServiceId(event.target.value)}
            >
              <option value="">Infer from log records</option>
              {servicesQuery.data?.items.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.name}
                </option>
              ))}
            </select>
          </label>

          {error ? (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          ) : null}

          <Button
            type="button"
            isLoading={uploadMutation.isPending}
            disabled={!file}
            onClick={() => uploadMutation.mutate()}
          >
            Upload and process
          </Button>

          {uploadMutation.isPending ? (
            <p className="text-xs text-slate-500">Uploading and processing…</p>
          ) : null}

          {result ? (
            <div className="rounded-md border border-graphite-700 bg-graphite-850/40 p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="accent">{result.status}</Badge>
                <span className="text-slate-400">Processed {result.processed_records}</span>
                <span className="text-slate-400">Failed {result.failed_records}</span>
              </div>
              {result.error_summary ? (
                <pre className="mt-2 max-h-32 overflow-auto text-xs text-amber-300/90">
                  {result.error_summary}
                </pre>
              ) : null}
              <Link
                className="mt-2 inline-block text-xs text-accent-cyan hover:underline"
                to={`/projects/${projectId}/logs`}
              >
                Open log explorer
              </Link>
            </div>
          ) : null}
        </CardBody>
      </Card>
    </div>
  );
}