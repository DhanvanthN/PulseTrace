import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.deployment import Deployment
from app.models.incident import Incident, IncidentEvent
from app.models.project import Project
from app.models.user import User
from app.modules.incidents.correlator import correlate_project_incidents
from app.modules.incidents.sanitize import sanitize_configuration_diff
from app.modules.incidents.validation import assert_service_in_project
from app.repositories.deployment_repository import DeploymentRepository
from app.repositories.incident_repository import IncidentFilters, IncidentRepository
from app.schemas.deployment import DeploymentCreateRequest, DeploymentListResponse, DeploymentResponse
from app.models.rca import RCAInvestigation, RootCauseCandidate
from app.modules.root_cause.engine import run_rca_investigation
from app.modules.root_cause.report import build_investigation_report, report_to_markdown
from app.schemas.incident import (
    IncidentCorrelateResponse,
    IncidentCreateRequest,
    IncidentDetailResponse,
    IncidentEvidenceListResponse,
    IncidentEvidenceResponse,
    IncidentEventResponse,
    IncidentListResponse,
    IncidentNoteRequest,
    IncidentResponse,
    IncidentTimelineResponse,
    IncidentUpdateRequest,
)
from app.schemas.rca import (
    InvestigationReportResponse,
    RCAInvestigateResponse,
    RootCauseCandidateResponse,
    RootCauseListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}", tags=["incidents"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    project_id: UUID,
    payload: IncidentCreateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    try:
        assert_service_in_project(db, payload.primary_service_id, project.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    started = payload.started_at or _utc_now()
    incident = Incident(
        project_id=project.id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        started_at=started,
        last_activity_at=started,
        primary_service_id=payload.primary_service_id,
        correlation_key=f"manual:{uuid.uuid4().hex}",
    )
    db.add(incident)
    db.flush()
    db.add(
        IncidentEvent(
            incident_id=incident.id,
            event_type="STATUS_CHANGED",
            description=f"Incident created manually ({payload.status}).",
            event_timestamp=started,
            event_metadata={"status": payload.status, "created_by": str(current_user.id)},
            dedupe_key=f"status:{incident.id}:create",
        )
    )
    db.commit()
    db.refresh(incident)
    return IncidentResponse.model_validate(incident)


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(
    project_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    service_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    filters = IncidentFilters(
        status=status_filter,
        severity=severity,
        service_id=service_id,
        search=search,
        start_time=start_time,
        end_time=end_time,
    )
    items, total, status_counts, severity_counts = IncidentRepository(db).search(
        project.id,
        filters,
        skip=skip,
        limit=limit,
    )
    return IncidentListResponse(
        items=[IncidentResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
        status_counts=status_counts,
        severity_counts=severity_counts,
    )


@router.post("/incidents/correlate", response_model=IncidentCorrelateResponse)
def correlate_incidents(
    project_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentCorrelateResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    try:
        result = correlate_project_incidents(db, project.id)
    except Exception as exc:
        logger.exception("Incident correlation failed project_id=%s", project.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Correlation failed") from exc
    return IncidentCorrelateResponse.model_validate(result)


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentDetailResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    payload = IncidentDetailResponse.model_validate(incident)
    payload.events_count = len(incident.events)
    payload.evidence_count = len(incident.evidence_items)
    return payload


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident(
    project_id: UUID,
    incident_id: UUID,
    payload: IncidentUpdateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    if payload.primary_service_id is not None:
        try:
            assert_service_in_project(db, payload.primary_service_id, project.id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        incident.primary_service_id = payload.primary_service_id

    previous_status = incident.status
    if payload.title is not None:
        incident.title = payload.title
    if payload.description is not None:
        incident.description = payload.description
    if payload.severity is not None:
        incident.severity = payload.severity
    if payload.status is not None:
        incident.status = payload.status
        now = _utc_now()
        incident.last_activity_at = now
        if payload.status == "RESOLVED":
            incident.resolved_at = now
        elif previous_status == "RESOLVED" and payload.status in {"OPEN", "INVESTIGATING"}:
            incident.resolved_at = None
        dedupe = f"status:{incident.id}:{payload.status}:{now.isoformat()}"
        db.add(
            IncidentEvent(
                incident_id=incident.id,
                event_type="STATUS_CHANGED",
                description=f"Status changed from {previous_status} to {payload.status}.",
                event_timestamp=now,
                event_metadata={"previous_status": previous_status, "status": payload.status},
                dedupe_key=dedupe,
            )
        )

    db.commit()
    db.refresh(incident)
    return IncidentResponse.model_validate(incident)


@router.get("/incidents/{incident_id}/timeline", response_model=IncidentTimelineResponse)
def incident_timeline(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentTimelineResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    events = IncidentRepository(db).timeline(incident.id)
    return IncidentTimelineResponse(
        items=[IncidentEventResponse.from_model(item) for item in events]
    )


@router.get("/incidents/{incident_id}/evidence", response_model=IncidentEvidenceListResponse)
def incident_evidence(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> IncidentEvidenceListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    items = IncidentRepository(db).evidence(incident.id)
    return IncidentEvidenceListResponse(
        items=[IncidentEvidenceResponse.model_validate(item) for item in items]
    )


@router.post("/incidents/{incident_id}/notes", response_model=IncidentEventResponse)
def add_incident_note(
    project_id: UUID,
    incident_id: UUID,
    payload: IncidentNoteRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentEventResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    now = _utc_now()
    dedupe = f"note:{incident.id}:{uuid.uuid4().hex}"
    event = IncidentEvent(
        incident_id=incident.id,
        event_type="INVESTIGATION_NOTE",
        description=payload.content,
        event_timestamp=now,
        event_metadata={"author_id": str(current_user.id)},
        dedupe_key=dedupe,
    )
    incident.last_activity_at = now
    db.add(event)
    db.commit()
    db.refresh(event)
    return IncidentEventResponse.from_model(event)


@router.post("/incidents/{incident_id}/investigate", response_model=RCAInvestigateResponse)
def investigate_incident(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> RCAInvestigateResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    try:
        result = run_rca_investigation(db, project_id=project.id, incident_id=incident.id)
    except Exception as exc:
        logger.exception("RCA failed incident_id=%s", incident.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RCA failed") from exc
    if result.get("status") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return RCAInvestigateResponse.model_validate(result)


@router.get("/incidents/{incident_id}/root-causes", response_model=RootCauseListResponse)
def list_root_causes(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> RootCauseListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    incident = IncidentRepository(db).get_in_project(incident_id, project.id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    investigation = db.scalars(
        select(RCAInvestigation)
        .where(RCAInvestigation.incident_id == incident.id)
        .order_by(RCAInvestigation.version.desc())
        .limit(1)
    ).first()
    if investigation is None:
        return RootCauseListResponse(
            investigation_id=None,
            version=None,
            status=None,
            items=[],
        )

    items = list(
        db.scalars(
            select(RootCauseCandidate)
            .where(RootCauseCandidate.investigation_id == investigation.id)
            .order_by(RootCauseCandidate.ranking.asc())
        ).all()
    )
    return RootCauseListResponse(
        investigation_id=investigation.id,
        version=investigation.version,
        status=investigation.status,
        items=[RootCauseCandidateResponse.model_validate(item) for item in items],
    )


@router.get(
    "/incidents/{incident_id}/root-causes/{candidate_id}",
    response_model=RootCauseCandidateResponse,
)
def get_root_cause(
    project_id: UUID,
    incident_id: UUID,
    candidate_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> RootCauseCandidateResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    candidate = db.scalar(
        select(RootCauseCandidate).where(
            RootCauseCandidate.id == candidate_id,
            RootCauseCandidate.incident_id == incident_id,
            RootCauseCandidate.incident.has(project_id=project.id),
        )
    )
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return RootCauseCandidateResponse.model_validate(candidate)


@router.get("/incidents/{incident_id}/investigation-report", response_model=InvestigationReportResponse)
def get_investigation_report(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> InvestigationReportResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    report = build_investigation_report(db, project_id=project.id, incident_id=incident_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return InvestigationReportResponse(report=report, markdown=report_to_markdown(report))


@router.get("/incidents/{incident_id}/investigation-report.md")
def export_investigation_report_markdown(
    project_id: UUID,
    incident_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> Response:
    report = build_investigation_report(db, project_id=project.id, incident_id=incident_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    body = report_to_markdown(report)
    return Response(content=body, media_type="text/markdown; charset=utf-8")


@router.post("/deployments", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
def create_deployment(
    project_id: UUID,
    payload: DeploymentCreateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> DeploymentResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    try:
        assert_service_in_project(db, payload.service_id, project.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    deployment = Deployment(
        project_id=project.id,
        service_id=payload.service_id,
        version=payload.version,
        change_type=payload.change_type,
        description=payload.description,
        configuration_diff=sanitize_configuration_diff(payload.configuration_diff),
        deployed_at=payload.deployed_at or _utc_now(),
    )
    DeploymentRepository(db).create(deployment)
    db.commit()
    db.refresh(deployment)
    return DeploymentResponse.model_validate(deployment)


@router.get("/deployments", response_model=DeploymentListResponse)
def list_deployments(
    project_id: UUID,
    service_id: UUID | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> DeploymentListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    items, total = DeploymentRepository(db).list_project(
        project.id,
        service_id=service_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    return DeploymentListResponse(
        items=[DeploymentResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )