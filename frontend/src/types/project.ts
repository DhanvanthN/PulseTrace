export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  environment: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  skip: number;
  limit: number;
}

export interface ProjectCreatePayload {
  name: string;
  description?: string | null;
  environment: string;
}

export interface ProjectUpdatePayload {
  name?: string;
  description?: string | null;
  environment?: string;
}