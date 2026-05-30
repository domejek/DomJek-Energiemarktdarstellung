import { Component, Input, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

declare const Plotly: any;

@Component({
  selector: 'app-time-series-chart',
  standalone: true,
  imports: [CommonModule],
  template: `<div #chart style="width:100%;height:450px"></div>`,
  styles: [`div { margin: 1rem 0; }`],
})
export class TimeSeriesChartComponent implements OnChanges {
  @ViewChild('chart') chartEl!: ElementRef;
  @Input() data: any[] = [];
  @Input() chartType: 'prl' | 'affr' = 'prl';
  @Input() showGesamt = true;
  @Input() tsos: any = {};

  ngOnChanges(): void {
    setTimeout(() => this.buildChart());
  }

  private buildChart(): void {
    if (!this.data.length || !this.chartEl) return;
    const traces: any[] = [];

    if (this.showGesamt) {
      if (this.chartType === 'prl') {
        traces.push(
          this.trace(this.data, 'deutschland_positiv_mw', 'Deutschland Positiv', 'green', 2),
          this.trace(this.data, 'deutschland_negativ_mw', 'Deutschland Negativ', 'red', 2)
        );
      } else {
        traces.push(
          this.trace(this.data, 'deutschland_positiv_mw', 'Deutschland Positiv', 'blue', 2, 'tozeroy')
        );
      }
    }

    if (this.chartType === 'prl') {
      if (this.tsos._50hertz) traces.push(this.trace(this.data, '_50hertz_mw', '50Hertz', '#888', 1, undefined, 'dash'));
      if (this.tsos.amprion) traces.push(this.trace(this.data, 'amprion_mw', 'Amprion', '#888', 1, undefined, 'dash'));
      if (this.tsos.tennet) traces.push(this.trace(this.data, 'tennet_mw', 'TenneT', '#888', 1, undefined, 'dash'));
      if (this.tsos.transnetbw) traces.push(this.trace(this.data, 'transnetbw_mw', 'TransnetBW', '#888', 1, undefined, 'dash'));
    } else {
      if (this.tsos._50hertz) traces.push(this.trace(this.data, '_50hertz_positiv_mw', '50Hertz', '#888', 1, undefined, 'dash'));
      if (this.tsos.amprion) traces.push(this.trace(this.data, 'amprion_positiv_mw', 'Amprion', '#888', 1, undefined, 'dash'));
    }

    Plotly.newPlot(
      this.chartEl.nativeElement,
      traces,
      {
        title: this.chartType === 'prl' ? "k*Delta f (PRL) - Primärregelleistung" : 'Aktivierte aFRR (SRL) - Sekundärregelleistung',
        xaxis: { title: 'Zeitpunkt' },
        yaxis: { title: 'Leistung (MW)' },
        hovermode: 'x unified' as const,
        height: 450,
        legend: { orientation: 'h' as const, y: 1.1, x: 1, xanchor: 'right' as const },
      },
      { responsive: true }
    );
  }

  private trace(data: any[], key: string, name: string, color: string, width: number, fill?: string, dash?: string): any {
    const t: any = {
      x: data.map((d) => d.timestamp),
      y: data.map((d) => d[key] ?? 0),
      type: 'scatter',
      mode: 'lines',
      name,
      line: { color, width },
    };
    if (fill) t.fill = fill;
    if (dash) t.line.dash = dash;
    return t;
  }
}
