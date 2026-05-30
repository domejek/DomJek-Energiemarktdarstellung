import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-data-export',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './data-export.component.html',
})
export class DataExportComponent {
  @Input() prlData: any[] = [];
  @Input() affrData: any[] = [];
  @Input() showPrl = true;
  @Input() showAffr = true;
  @Input() startDate = '';
  @Input() endDate = '';

  downloadCsv(data: any[], filename: string): void {
    if (!data.length) return;
    const header = Object.keys(data[0]).join(',');
    const rows = data.map((r) => Object.values(r).join(','));
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
