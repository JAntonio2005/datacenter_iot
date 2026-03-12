import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';

export interface RackSummary {
  zone: string;
  rack: string;
  state: string;
  updated_at: string | null;
  temp_c: number | null;
  hum_pct: number | null;
  power_w: number | null;
}

export interface RackContainerMetric {
  container_name: string;
  host: string | null;
  cpu_pct: number | null;
  ram_mb: number | null;
  net_rx: number | null;
  net_tx: number | null;
  io_read: number | null;
  io_write: number | null;
  temp_c: number | null;
  hum_pct: number | null;
  power_w: number | null;
  ts: string | null;
}

export interface RackDetail {
  zone: string;
  rack: string;
  state: string;
  updated_at: string | null;
  ambient: {
    temp_c: number | null;
    hum_pct: number | null;
    power_w: number | null;
  };
  containers: RackContainerMetric[];
}

@Injectable({
  providedIn: 'root',
})
export class RacksService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiBaseUrl;

  getRacks(): Observable<RackSummary[]> {
    return this.http.get<RackSummary[]>(`${this.apiUrl}/racks`);
  }

  getRackDetail(zone: string, rack: string): Observable<RackDetail> {
    return this.http.get<RackDetail>(`${this.apiUrl}/racks/${zone}/${rack}`);
  }
}