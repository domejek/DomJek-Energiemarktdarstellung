export interface FilterState {
  dataSource: 'demo' | 'csv' | 'api';
  startDate: string;
  endDate: string;
  showPrl: boolean;
  showAffr: boolean;
  showGesamt: boolean;
  tsos: {
    _50hertz: boolean;
    amprion: boolean;
    tennet: boolean;
    transnetbw: boolean;
  };
}

export interface PrlRecord {
  timestamp: string;
  deutschland_positiv_mw: number;
  deutschland_negativ_mw: number;
  _50hertz_mw?: number;
  amprion_mw?: number;
  tennet_mw?: number;
  transnetbw_mw?: number;
}

export interface AffrRecord {
  timestamp: string;
  deutschland_positiv_mw: number;
  deutschland_negativ_mw: number;
  _50hertz_positiv_mw?: number;
  amprion_positiv_mw?: number;
  tennet_positiv_mw?: number;
  transnetbw_positiv_mw?: number;
}

export interface PrlResponse {
  data: PrlRecord[];
  metadata: { interval_count: number; source: string };
}

export interface AffrResponse {
  data: AffrRecord[];
  metadata: { interval_count: number; source: string };
}

export interface Statistics {
  prl: {
    mean_positive: number;
    mean_negative: number;
    max_positive: number;
    max_negative: number;
    std_positive: number;
    total_intervals: number;
  };
  affr: {
    mean_activation: number;
    max_activation: number;
    total_activated_mwh: number;
    activation_rate: number;
  };
}

export interface DailySummary {
  prl_daily: Array<{
    date: string;
    pos_mean: number;
    pos_max: number;
    pos_min: number;
    neg_mean: number;
    neg_max: number;
    neg_min: number;
  }>;
  affr_daily: Array<{
    date: string;
    pos_mean: number;
    pos_max: number;
    pos_sum: number;
    neg_mean: number;
    neg_max: number;
    neg_sum: number;
  }>;
}

export interface UploadResponse {
  success: boolean;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
}
