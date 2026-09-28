export type SystemRole =
  | "STATE_ADMIN"
  | "DEPARTMENT_ADMIN"
  | "CIRCLE_DIVISION_OFFICER"
  | "SUB_DIVISION_OFFICER"
  | "FIELD_ENGINEER"
  | "MAINTENANCE_OFFICER"
  | "CONTRACTOR"
  | "AUDITOR";

export type AssetTypeCode = "ROAD" | "BRIDGE" | "CULVERT" | "BUILDING" | "PUBLIC_STRUCTURE" | "OTHER_FIXED_ASSET";

export type LifecycleStatus =
  | "PLANNED"
  | "SANCTIONED"
  | "UNDER_CONSTRUCTION"
  | "COMMISSIONED"
  | "OPERATIONAL"
  | "INSPECTION_REQUIRED"
  | "MAINTENANCE_REQUIRED"
  | "UNDER_MAINTENANCE"
  | "RENOVATION_UPGRADATION"
  | "RETIRED"
  | "DECOMMISSIONED";

export type ConditionRating = "GOOD" | "FAIR" | "POOR" | "CRITICAL";

export type InspectionStatus = "ASSIGNED" | "IN_PROGRESS" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "RETURNED";

export type FindingSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type MaintenanceType = "PREVENTIVE" | "CORRECTIVE" | "EMERGENCY";
export type MaintenancePriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";
export type MaintenanceRequestStatus = "OPEN" | "APPROVED" | "REJECTED" | "CONVERTED_TO_WORK_ORDER" | "CLOSED";
export type WorkOrderStatus = "CREATED" | "ASSIGNED" | "IN_PROGRESS" | "COMPLETED" | "VERIFIED" | "CLOSED" | "CANCELLED";

export type ProjectStatus = "PROPOSED" | "SANCTIONED" | "IN_PROGRESS" | "COMPLETED" | "CLOSED";

export type DocumentType =
  | "LAND_RECORD"
  | "OWNERSHIP"
  | "DPR"
  | "DRAWING"
  | "APPROVAL"
  | "ESTIMATE"
  | "COMPLETION_CERTIFICATE"
  | "INSPECTION_REPORT"
  | "MAINTENANCE_REPORT"
  | "PHOTOGRAPH"
  | "OTHER";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  department_id: string | null;
  administrative_unit_id: string | null;
  roles: SystemRole[];
}

export interface Department {
  id: string;
  code: string;
  name: string;
  description: string | null;
}

export interface AdministrativeUnit {
  id: string;
  code: string;
  name: string;
  level: string;
  parent_id: string | null;
  path: string;
}

export interface AssetType {
  id: string;
  code: AssetTypeCode;
  name: string;
  default_geometry_kind: "POINT" | "LINESTRING" | "POLYGON";
  category_id: string | null;
}

export interface GeoJSONGeometry {
  type: "Point" | "LineString" | "Polygon";
  coordinates: unknown;
}

export interface RoadDetail {
  length_km?: number | null;
  width_m?: number | null;
  number_of_lanes?: number | null;
  surface_type?: string | null;
  start_point_desc?: string | null;
  end_point_desc?: string | null;
  traffic_info?: string | null;
}

export interface BridgeDetail {
  length_m?: number | null;
  width_m?: number | null;
  number_of_spans?: number | null;
  bridge_type?: string | null;
  material?: string | null;
  load_capacity_tonnes?: number | null;
}

export interface CulvertDetail {
  culvert_type?: string | null;
  length_m?: number | null;
  opening_width_m?: number | null;
  material?: string | null;
}

export interface BuildingDetail {
  plot_area_sqm?: number | null;
  built_up_area_sqm?: number | null;
  number_of_floors?: number | null;
  construction_year?: number | null;
  building_type?: string | null;
  occupancy_use?: string | null;
}

export interface StructureDetail {
  structure_subtype?: string | null;
  attributes?: Record<string, unknown> | null;
}

export interface AssetListItem {
  id: string;
  asset_code: string;
  name: string;
  asset_type_code: AssetTypeCode;
  lifecycle_status: LifecycleStatus;
  current_condition: ConditionRating | null;
  administrative_unit_id: string;
  department_id: string;
}

export interface Asset {
  id: string;
  asset_code: string;
  name: string;
  description: string | null;
  asset_type_code: AssetTypeCode;
  category_id: string | null;
  ownership: string | null;
  department_id: string;
  administrative_unit_id: string;
  address: string | null;
  acquisition_date: string | null;
  commissioning_date: string | null;
  lifecycle_status: LifecycleStatus;
  current_condition: ConditionRating | null;
  original_cost: number | null;
  current_value: number | null;
  useful_life_years: number | null;
  expected_end_of_life: string | null;
  responsible_officer_id: string | null;
  linked_project_id: string | null;
  created_at: string;
  updated_at: string;
  geometry: GeoJSONGeometry | null;
  road: RoadDetail | null;
  bridge: BridgeDetail | null;
  culvert: CulvertDetail | null;
  building: BuildingDetail | null;
  structure: StructureDetail | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface LifecycleEvent {
  id: string;
  old_status: LifecycleStatus | null;
  new_status: LifecycleStatus;
  changed_by: string;
  reason: string | null;
  created_at: string;
}

export interface InspectionFinding {
  id: string;
  description: string;
  severity: FindingSeverity;
  photo_document_ids: string[] | null;
  recommends_maintenance: boolean;
}

export interface Inspection {
  id: string;
  asset_id: string;
  inspector_id: string;
  assigned_date: string | null;
  inspection_date: string | null;
  overall_condition: ConditionRating | null;
  remarks: string | null;
  status: InspectionStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_comments: string | null;
  findings: InspectionFinding[];
  gps: GeoJSONGeometry | null;
}

export interface MaintenanceRequest {
  id: string;
  asset_id: string;
  source_inspection_finding_id: string | null;
  maintenance_type: MaintenanceType;
  priority: MaintenancePriority;
  description: string;
  estimated_cost: number | null;
  due_date: string | null;
  status: MaintenanceRequestStatus;
  requested_by: string;
  approved_by: string | null;
}

export interface WorkOrder {
  id: string;
  work_order_code: string;
  maintenance_request_id: string;
  asset_id: string;
  contractor_id: string | null;
  assigned_officer_id: string | null;
  priority: MaintenancePriority;
  status: WorkOrderStatus;
  sla_due_date: string | null;
  estimated_cost: number | null;
  actual_cost: number | null;
  completed_at: string | null;
  completion_remarks: string | null;
  verified_by: string | null;
  verified_at: string | null;
}

export interface Contractor {
  id: string;
  name: string;
  registration_number: string | null;
  contact_person: string | null;
  phone: string | null;
  email: string | null;
  address: string | null;
  is_active: boolean;
}

export interface Project {
  id: string;
  project_code: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  department_id: string;
  administrative_unit_id: string;
  sanctioned_budget: number | null;
  actual_expenditure: number | null;
  sanction_date: string | null;
  start_date: string | null;
  expected_completion_date: string | null;
  actual_completion_date: string | null;
  contractor_id: string | null;
}

export interface DocumentMeta {
  id: string;
  document_type: DocumentType;
  filename: string;
  mime_type: string;
  size_bytes: number;
  linked_entity_type: string;
  linked_entity_id: string;
  uploaded_by: string;
  current_version: number;
  created_at: string;
}

export interface DashboardData {
  total_assets: number;
  assets_by_type: Record<string, number>;
  assets_by_lifecycle_status: Record<string, number>;
  assets_by_condition: Record<string, number>;
  assets_by_administrative_unit: Record<string, number>;
  critical_assets: number;
  total_asset_value: number;
  inspections_due_soon: number;
  inspections_overdue: number;
  maintenance_due_soon: number;
  overdue_work_orders: number;
  active_maintenance: number;
  maintenance_expenditure: number;
  projects_in_progress: number;
  projects_completed: number;
}

export interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  event: string;
  title: string;
  body: string | null;
  context: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}
