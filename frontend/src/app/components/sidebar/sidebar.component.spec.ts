import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { SidebarComponent } from './sidebar.component';
import { FilterStateService } from '../../services/filter-state.service';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;
  let filterService: FilterStateService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SidebarComponent, NoopAnimationsModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [FilterStateService],
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    filterService = TestBed.inject(FilterStateService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should update filter on data source change', () => {
    spyOn(filterService, 'updateFilter').and.callThrough();
    component.setDataSource('csv');
    expect(filterService.updateFilter).toHaveBeenCalledWith({ dataSource: 'csv' });
    expect(component.filter.dataSource).toBe('csv');
  });

  it('should toggle PRL visibility', () => {
    component.togglePrl(false);
    expect(component.filter.showPrl).toBeFalse();
  });

  it('should toggle single TSO', () => {
    component.toggleTso('amprion', true);
    expect(component.filter.tsos.amprion).toBeTrue();
    expect(component.filter.tsos._50hertz).toBeFalse();
  });
});
