import { Component, Input, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

declare const Plotly: any;

@Component({
  selector: 'app-daily-profile-chart',
  standalone: true,
  imports: [CommonModule],
  template: `<div #chart style="width:100%;height:400px"></div>`,
})
export class DailyProfileChartComponent implements OnChanges {
  @ViewChild('chart') chartEl!: ElementRef;
  @Input() data: any[] = [];

  ngOnChanges(): void {
    setTimeout(() => this.buildChart());
  }

  private buildChart(): void {
    if (!this.data.length || !this.chartEl) return;

    const hourly: Record<number, { pos: number[]; neg: number[] }> = {};
    for (const d of this.data) {
      const h = new Date(d.timestamp).getHours();
      if (!hourly[h]) hourly[h] = { pos: [], neg: [] };
      hourly[h].pos.push(d.deutschland_positiv_mw ?? 0);
      hourly[h].neg.push(d.deutschland_negativ_mw ?? 0);
    }

    const hours = Object.keys(hourly).map(Number).sort();
    const posAvg = hours.map((h) => hourly[h].pos.reduce((a, b) => a + b, 0) / hourly[h].pos.length);
    const negAvg = hours.map((h) => hourly[h].neg.reduce((a, b) => a + b, 0) / hourly[h].neg.length);

    Plotly.newPlot(
      this.chartEl.nativeElement,
      [
        { x: hours, y: posAvg, type: 'scatter', mode: 'lines+markers', name: 'Ø Positiv', line: { color: 'green' } },
        { x: hours, y: negAvg, type: 'scatter', mode: 'lines+markers', name: 'Ø Negativ', line: { color: 'red' } },
      ],
      {
        title: 'PRL Tagesprofil',
        xaxis: { title: 'Stunde des Tages', dtick: 2 },
        yaxis: { title: 'Durchschnittliche Leistung (MW)' },
        height: 400,
      },
      { responsive: true }
    );
  }
}
