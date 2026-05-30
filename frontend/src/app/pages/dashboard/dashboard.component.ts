import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { FilterStateService } from '../../services/filter-state.service';
import { EnergyDataService } from '../../services/energy-data.service';
import { FilterState, Statistics } from '../../models/energy-data.model';

import { SidebarComponent } from '../../components/sidebar/sidebar.component';
import { KpiCardsComponent } from '../../components/kpi-cards/kpi-cards.component';
import { TimeSeriesChartComponent } from '../../components/charts/time-series-chart/time-series-chart.component';
import { DistributionChartComponent } from '../../components/charts/distribution-chart/distribution-chart.component';
import { DailyProfileChartComponent } from '../../components/charts/daily-profile-chart/daily-profile-chart.component';
import { HeatmapChartComponent } from '../../components/charts/heatmap-chart/heatmap-chart.component';
import { CsvUploadComponent } from '../../components/csv-upload/csv-upload.component';
import { DataExportComponent } from '../../components/data-export/data-export.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    SidebarComponent,
    KpiCardsComponent,
    TimeSeriesChartComponent,
    DistributionChartComponent,
    DailyProfileChartComponent,
    HeatmapChartComponent,
    CsvUploadComponent,
    DataExportComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit, OnDestroy {
  filter!: FilterState;
  statistics: Statistics | null = null;
  prlData: any[] = [];
  affrData: any[] = [];
  dailySummary: any = null;
  loading = true;

  sourceLabel = '';
  fallbackDate: string | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private filterService: FilterStateService,
    private dataService: EnergyDataService
  ) {}

  ngOnInit(): void {
    this.filterService.filterState$
      .pipe(takeUntil(this.destroy$))
      .subscribe((state: FilterState) => {
        this.filter = state;
        this.loadData();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private parseSource(metadata: { source: string }): void {
    const src = metadata.source;

    if (src === 'demo') {
      this.sourceLabel = 'Demo-Daten';
      this.fallbackDate = null;
    } else if (src === 'api') {
      this.sourceLabel = 'regelleistung.net';
      this.fallbackDate = null;
    } else if (src.startsWith('api_fallback_')) {
      this.sourceLabel = 'regelleistung.net';
      this.fallbackDate = src.replace('api_fallback_', '');
    } else if (src === 'demo_fallback') {
      this.sourceLabel = 'Demo-Daten (API nicht verfügbar)';
      this.fallbackDate = null;
    } else {
      this.sourceLabel = src;
      this.fallbackDate = null;
    }
  }

  private loadData(): void {
    this.loading = true;

    this.dataService.getPrlData(this.filter).subscribe({
      next: (res) => {
        this.prlData = res.data;
        this.parseSource(res.metadata);
      },
    });

    this.dataService.getAffrData(this.filter).subscribe({
      next: (res) => (this.affrData = res.data),
    });

    this.dataService.getStatistics(this.filter).subscribe({
      next: (res) => (this.statistics = res),
    });

    this.dataService.getDailySummary(this.filter).subscribe({
      next: (res) => (this.dailySummary = res),
    });

    this.loading = false;
  }
}
