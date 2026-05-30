import { TestBed } from '@angular/core/testing';
import { FilterStateService } from './filter-state.service';
import { FilterState } from '../models/energy-data.model';

describe('FilterStateService', () => {
  let service: FilterStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [FilterStateService] });
    service = TestBed.inject(FilterStateService);
  });

  it('should have default filter state with api source', (done) => {
    service.filterState$.subscribe((state) => {
      expect(state.dataSource).toBe('api');
      expect(state.showPrl).toBeTrue();
      expect(state.showAffr).toBeTrue();
      expect(state.showGesamt).toBeTrue();
      done();
    });
  });

  it('should update filter with partial data', (done) => {
    service.updateFilter({ showPrl: false });
    service.filterState$.subscribe((state) => {
      expect(state.showPrl).toBeFalse();
      expect(state.showAffr).toBeTrue();
      done();
    });
  });

  it('should reset to defaults', (done) => {
    service.updateFilter({ dataSource: 'csv', showPrl: false });
    service.resetFilter();
    service.filterState$.subscribe((state) => {
      expect(state.dataSource).toBe('api');
      expect(state.showPrl).toBeTrue();
      done();
    });
  });

  it('should provide snapshot of current state', () => {
    expect(service.snapshot.dataSource).toBe('api');
    service.updateFilter({ dataSource: 'demo' });
    expect(service.snapshot.dataSource).toBe('demo');
  });
});
