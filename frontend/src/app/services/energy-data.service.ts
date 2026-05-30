import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  FilterState,
  PrlResponse,
  AffrResponse,
  Statistics,
  DailySummary,
  UploadResponse,
} from '../models/energy-data.model';

@Injectable({ providedIn: 'root' })
export class EnergyDataService {
  private base = '/api/energy';

  constructor(private http: HttpClient) {}

  getPrlData(filter: FilterState): Observable<PrlResponse> {
    return this.http.get<PrlResponse>(`${this.base}/prl`, {
      params: this.buildParams(filter),
    });
  }

  getAffrData(filter: FilterState): Observable<AffrResponse> {
    return this.http.get<AffrResponse>(`${this.base}/affr`, {
      params: this.buildParams(filter),
    });
  }

  getStatistics(filter: FilterState): Observable<Statistics> {
    return this.http.get<Statistics>(`${this.base}/statistics`, {
      params: this.buildParams(filter),
    });
  }

  getDailySummary(filter: FilterState): Observable<DailySummary> {
    return this.http.get<DailySummary>(`${this.base}/daily-summary`, {
      params: this.buildParams(filter),
    });
  }

  uploadCsv(file: File, type: 'prl' | 'affr'): Observable<UploadResponse> {
    const fd = new FormData();
    fd.append('file', file);
    const params = new HttpParams().set('type', type);
    return this.http.post<UploadResponse>(`${this.base}/upload`, fd, {
      params,
    });
  }

  private buildParams(filter: FilterState): HttpParams {
    return new HttpParams()
      .set('start', filter.startDate)
      .set('end', filter.endDate)
      .set('source', filter.dataSource);
  }
}
