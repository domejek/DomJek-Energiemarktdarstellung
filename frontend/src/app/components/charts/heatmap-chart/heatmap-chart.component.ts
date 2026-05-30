import { Component, Input, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

declare const Plotly: any;

@Component({
  selector: 'app-heatmap-chart',
  standalone: true,
  imports: [CommonModule],
  template: `<div #chart style="width:100%;height:400px"></div>`,
})
export class HeatmapChartComponent implements OnChanges {
  @ViewChild('chart') chartEl!: ElementRef;
  @Input() data: any[] = [];

  private readonly days = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

  ngOnChanges(): void {
    setTimeout(() => this.buildChart());
  }

  private buildChart(): void {
    if (!this.data.length || !this.chartEl) return;

    const grid: Record<number, Record<number, number[]>> = {};
    for (const d of this.data) {
      const dt = new Date(d.timestamp);
      const hour = dt.getHours();
      const wd = dt.getDay();
      if (!grid[wd]) grid[wd] = {};
      if (!grid[wd][hour]) grid[wd][hour] = [];
      grid[wd][hour].push(d.deutschland_positiv_mw ?? 0);
    }

    const hours = Array.from({ length: 24 }, (_, i) => i);
    const z = this.days.map((_, di) =>
      hours.map((h) => {
        const vals = grid[di + 1]?.[h] || grid[di === 6 ? 0 : di + 1]?.[h] || [];
        return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      })
    );

    Plotly.newPlot(
      this.chartEl.nativeElement,
      [{ z, x: hours, y: this.days, type: 'heatmap', colorscale: 'YlOrRd' }],
      {
        title: 'aFRR Aktivierungs-Heatmap',
        xaxis: { title: 'Stunde', dtick: 2 },
        yaxis: { title: 'Wochentag' },
        height: 400,
      },
      { responsive: true }
    );
  }
}
