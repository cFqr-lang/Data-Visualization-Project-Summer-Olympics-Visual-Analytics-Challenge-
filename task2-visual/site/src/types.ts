export interface FigureMeta {
  figure_id: string;
  chart_id: string;
  title: string;
  caliber: string;
  caliber_label: string;
  denominator: string;
  includes_1906: boolean;
  data_version: string;
  generated_at: string;
  source: string;
  event_key_source: string;
  notes: string[];
}

export interface RankRow {
  noc: string;
  gold: number;
  silver: number;
  bronze: number;
  total: number;
  rank: number;
}

export interface A1Total extends RankRow {
  athlete_medal_rows: number;
  diff: number;
}

export interface A1Definition {
  id: string;
  label: string;
  caliber: string;
  includes_1906: boolean;
  ranking: RankRow[];
}

export interface A1Payload {
  meta: FigureMeta;
  totals_top20: A1Total[];
  definitions: A1Definition[];
  rank_changes: { noc: string; athlete_row_rank: number; conservative_rank: number; delta: number }[];
}

export interface RaceRow extends RankRow {
  year: number;
}

export interface A2Point {
  year: number;
  medal_events: number;
  medal_rows: number;
  delegations: number;
  athletes: number;
  events_proxy: number;
  events_official: number | null;
  index: { medals: number; delegations: number; athletes: number; events: number };
}

export interface A2Payload {
  meta: FigureMeta;
  series: A2Point[];
  bar_race: { year: number; top: RaceRow[] }[];
  snapshots: { year: number; top: RaceRow[] }[];
  missing_years: number[];
}

export interface B1Point {
  year: number;
  gold: number;
  silver: number;
  bronze: number;
  total: number;
}

export interface B1Panel {
  key: string;
  label: string;
  nocs: string[];
  series: { noc: string; points: B1Point[] }[];
  notes: string[];
}

export interface B1Payload {
  meta: FigureMeta;
  panels: B1Panel[];
}

export interface C1Point {
  year: number;
  male_rows: number;
  female_rows: number;
  female_share: number;
  delegations: number;
  delegations_with_women: number;
  women_events: number;
  men_events: number;
  mixed_events: number;
}

export interface C1Payload {
  meta: FigureMeta;
  series: C1Point[];
  milestones: { year: number; text: string }[];
}

export interface C2Point {
  noc: string;
  rows: number;
  female_share: number;
  female_medals: number;
  male_medals: number;
  mixed_medals: number;
  female_medal_share: number | null;
}

export interface C2View {
  id: string;
  label: string;
  years: number[];
  min_rows: number;
  min_medals: number;
  points: C2Point[];
}

export interface C2Payload {
  meta: FigureMeta;
  views: C2View[];
}

export interface D1Sport {
  sport: string;
  first: number;
  last: number;
  editions: number;
  medals: number;
  status: 'active' | 'retired';
}

export interface D1Payload {
  meta: FigureMeta;
  sports: D1Sport[];
  event_counts: { year: number; proxy: number; official: number | null }[];
  highlights: { retired: D1Sport[]; added: D1Sport[] };
}

export interface B2Point {
  noc: string;
  editions: number;
  total_medals: number;
  avg_athletes: number;
  avg_medals: number;
  efficiency: number;
  rank: number;
}

export interface B2Payload {
  meta: FigureMeta;
  points: B2Point[];
}

export interface D2Payload {
  meta: FigureMeta;
  categories: string[];
  river: [string, number, string][];
  totals: { name: string; medals: number }[];
}

export interface X1Cell {
  noc: string;
  sport: string;
  medals: number;
  lift: number;
}

export interface X1Payload {
  meta: FigureMeta;
  nocs: { noc: string; medals: number }[];
  sports: { sport: string; medals: number }[];
  cells: X1Cell[];
  max_lift: number;
}

export interface X2Sport {
  sport: string;
  female_athletes: number;
  male_athletes: number;
  athletes: number;
  female_share: number;
  male_share: number;
  gap_pp: number;
  medal_rows: number;
  female_medal_share: number | null;
  rank: number;
}

export interface X2Payload {
  meta: FigureMeta;
  year: number;
  sports: X2Sport[];
}

export interface IndexPayload {
  schema: string;
  data_version: string;
  generated_at: string;
  figures: { figure_id: string; chart_id: string; title: string; path: string; caliber: string }[];
}

export interface MetaPayload {
  data_version: string;
  generated_at: string;
  counts: Record<string, number | string>;
  checks: { check: string; expected: unknown; actual: unknown; pass: boolean }[];
}
