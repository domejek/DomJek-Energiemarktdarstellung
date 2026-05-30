import { Component, Input, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

declare const Plotly: any;

@Component({
  selector: 'app-distribution-chart',
  standalone: true,
  imports: [CommonModule],
  template: `<div #chart style="width:100%;height:350px"></div>`,
})
export class DistributionChartComponent implements OnChanges {
  @ViewChild('chart') chartEl!: ElementRef;
  @Input() data: any[] = [];
  @Input() title = '';

  ngOnChanges(): void {
    setTimeout(() => this.buildChart());
  }

  private buildChart(): void {
    if (!this.data.length || !this.chartEl) return;
    const values = this.data.map((d) => d.deutschland_positiv_mw ?? 0);

    Plotly.newPlot(
      this.chartEl.nativeElement,
      [{ x: values, type: 'histogram', nbinsx: 50, marker: { color: '#2196f3' } }],
      { title: this.title, xaxis: { title: 'Leistung (MW)' }, yaxis: { title: 'Häufigkeit' }, height: 350 },
      { responsive: true }
    );
  }
}
