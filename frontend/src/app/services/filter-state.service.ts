import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { FilterState } from '../models/energy-data.model';

const DEFAULT_FILTER: FilterState = {
  dataSource: 'api',
  startDate: '',
  endDate: '',
  showPrl: true,
  showAffr: true,
  showGesamt: true,
  tsos: {
    _50hertz: false,
    amprion: false,
    tennet: false,
    transnetbw: false,
  },
};

@Injectable({ providedIn: 'root' })
export class FilterStateService {
  private state = new BehaviorSubject<FilterState>({
    ...DEFAULT_FILTER,
    startDate: this.daysAgo(7),
    endDate: this.today(),
  });

  readonly filterState$: Observable<FilterState> = this.state.asObservable();

  get snapshot(): FilterState {
    return this.state.getValue();
  }

  updateFilter(partial: Partial<FilterState>): void {
    this.state.next({ ...this.snapshot, ...partial });
  }

  resetFilter(): void {
    this.state.next({
      ...DEFAULT_FILTER,
      startDate: this.daysAgo(7),
      endDate: this.today(),
    });
  }

  private today(): string {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }

  private daysAgo(n: number): string {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().slice(0, 10);
  }
}
