import { Navigate, Route, Routes } from "react-router-dom";

import { AuthLayout } from "@/components/layout/AuthLayout";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/routing/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { OverviewPage } from "@/features/dashboard/OverviewPage";
import { ProjectDetailPage } from "@/features/projects/ProjectDetailPage";
import { LogExplorerPage } from "@/features/logs/LogExplorerPage";
import { LogHubPage } from "@/features/logs/LogHubPage";
import { LogUploadPage } from "@/features/logs/LogUploadPage";
import { AnalysisDashboardPage } from "@/features/analysis/AnalysisDashboardPage";
import { AnomalyExplorerPage } from "@/features/analysis/AnomalyExplorerPage";
import { ClusterExplorerPage } from "@/features/analysis/ClusterExplorerPage";
import { IncidentsHubPage } from "@/features/analysis/IncidentsHubPage";
import { IncidentDashboardPage } from "@/features/incidents/IncidentDashboardPage";
import { IncidentDetailPage } from "@/features/incidents/IncidentDetailPage";
import { IncidentExplorerPage } from "@/features/incidents/IncidentExplorerPage";
import { InvestigationsHubPage } from "@/features/incidents/InvestigationsHubPage";
import { ProjectsPage } from "@/features/projects/ProjectsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/logs" element={<LogHubPage />} />
          <Route path="/projects/:projectId/logs" element={<LogExplorerPage />} />
          <Route path="/projects/:projectId/logs/upload" element={<LogUploadPage />} />
          <Route path="/incidents" element={<IncidentsHubPage />} />
          <Route path="/projects/:projectId/analysis" element={<AnalysisDashboardPage />} />
          <Route path="/projects/:projectId/anomalies" element={<AnomalyExplorerPage />} />
          <Route path="/projects/:projectId/clusters" element={<ClusterExplorerPage />} />
          <Route path="/investigations" element={<InvestigationsHubPage />} />
          <Route path="/projects/:projectId/incidents" element={<IncidentDashboardPage />} />
          <Route path="/projects/:projectId/incidents/explore" element={<IncidentExplorerPage />} />
          <Route path="/projects/:projectId/incidents/:incidentId" element={<IncidentDetailPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}