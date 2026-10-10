export interface RunSummary {
  total_records: number
  valid_records: number
  rejected_records: number
  duplicates_detected: number
  input_file?: string
  processed_at?: string
}

export interface RunListItem extends RunSummary {
  run_id: string
}

export type Row = Record<string, string>

export interface RunDetail {
  run_id: string
  summary: RunSummary
  cleaned: Row[]
  rejected: Row[]
}

export interface UploadResult {
  run_id: string
  summary: RunSummary
}

export type ReportKind = 'cleaned' | 'rejected' | 'summary' | 'input'
