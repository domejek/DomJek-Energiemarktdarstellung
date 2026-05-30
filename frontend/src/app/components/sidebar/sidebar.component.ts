import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatRadioModule } from '@angular/material/radio';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { FilterStateService } from '../../services/filter-state.service';
import { FilterState } from '../../models/energy-data.model';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatRadioModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatCheckboxModule,
    MatDividerModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  constructor(private filterService: FilterStateService) {}

  get filter(): FilterState {
    return this.filterService.snapshot;
  }

  setDataSource(source: string): void {
    this.filterService.updateFilter({ dataSource: source as FilterState['dataSource'] });
  }

  onStartDateChange(value: string | null): void {
    if (value) {
      this.filterService.updateFilter({ startDate: this.formatDate(value) });
    }
  }

  onEndDateChange(value: string | null): void {
    if (value) {
      this.filterService.updateFilter({ endDate: this.formatDate(value) });
    }
  }

  togglePrl(checked: boolean): void {
    this.filterService.updateFilter({ showPrl: checked });
  }

  toggleAffr(checked: boolean): void {
    this.filterService.updateFilter({ showAffr: checked });
  }

  toggleGesamt(checked: boolean): void {
    this.filterService.updateFilter({ showGesamt: checked });
  }

  toggleTso(tso: keyof FilterState['tsos'], checked: boolean): void {
    this.filterService.updateFilter({
      tsos: { ...this.filter.tsos, [tso]: checked },
    });
  }

  private formatDate(d: string): string {
    return d.slice(0, 10);
  }
}
