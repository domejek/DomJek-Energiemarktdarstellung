import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { EnergyDataService } from '../../services/energy-data.service';
import { UploadResponse } from '../../models/energy-data.model';

@Component({
  selector: 'app-csv-upload',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule, MatTableModule],
  templateUrl: './csv-upload.component.html',
})
export class CsvUploadComponent {
  result: UploadResponse | null = null;
  error = '';
  uploading = false;

  constructor(private dataService: EnergyDataService) {}

  onFileSelected(event: Event, type: 'prl' | 'affr'): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    this.uploading = true;
    this.error = '';
    this.result = null;

    this.dataService.uploadCsv(input.files[0], type).subscribe({
      next: (res) => {
        this.result = res;
        this.uploading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Upload fehlgeschlagen';
        this.uploading = false;
      },
    });
  }

  displayedColumns(): string[] {
    return this.result?.columns || [];
  }
}
