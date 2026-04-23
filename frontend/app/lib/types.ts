export interface GpsData {
  lat: number;
  lon: number;
  altitude?: number;
}

export interface ImageFindings {
  gps?: GpsData | null;
  camera?: Record<string, unknown>;
  timestamps?: Record<string, unknown>;
  author?: string | null;
  thumbnail_embedded?: boolean;
  raw_exif?: Record<string, unknown>;
}

export interface PdfFindings {
  author?: string | null;
  creator_tool?: string | null;
  producer?: string | null;
  title?: string | null;
  subject?: string | null;
  keywords?: string | null;
  creation_date?: string | null;
  modification_date?: string | null;
  pages?: number;
  pdf_version?: string | null;
  has_javascript?: boolean;
  embedded_file_count?: number;
  has_incremental_updates?: boolean;
  form_fields?: string[];
  embedded_fonts?: string[];
  raw_metadata?: Record<string, unknown>;
}

export interface DocxFindings {
  author?: string | null;
  last_modified_by?: string | null;
  title?: string | null;
  subject?: string | null;
  description?: string | null;
  keywords?: string | null;
  category?: string | null;
  revision?: number;
  created?: string | null;
  modified?: string | null;
  company?: string | null;
  app_name?: string | null;
  app_version?: string | null;
  total_editing_time?: string | null;
  tracked_changes_count?: number;
  comments_count?: number;
  embedded_image_count?: number;
  raw_core_props?: Record<string, unknown>;
  raw_app_props?: Record<string, unknown>;
}

export interface AuditResponse {
  filename: string;
  file_size: number;
  file_type: string;
  findings: ImageFindings | PdfFindings | DocxFindings;
  sensitivity_score: number;
  risks: string[];
  cleaned_file_id?: string;
  cleaned_size?: number;
  strip_error?: string;
  error?: string;
}
