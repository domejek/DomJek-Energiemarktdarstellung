import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { DashboardComponent } from './dashboard.component';
import { FilterStateService } from '../../services/filter-state.service';
import { EnergyDataService } from '../../services/energy-data.service';
import { provideHttpClient } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { of } from 'rxjs';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let dataSpy: jasmine.SpyObj<EnergyDataService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('EnergyDataService', ['getPrlData', 'getAffrData', 'getStatistics', 'getDailySummary']);
    spy.getPrlData.and.returnValue(of({ data: [], metadata: { interval_count: 0, source: '' } }));
    spy.getAffrData.and.returnValue(of({ data: [], metadata: { interval_count: 0, source: '' } }));
    spy.getStatistics.and.returnValue(of({ prl: { mean_positive: 0, mean_negative: 0, max_positive: 0, max_negative: 0, std_positive: 0, total_intervals: 0 }, affr: { mean_activation: 0, max_activation: 0, total_activated_mwh: 0, activation_rate: 0 } }));
    spy.getDailySummary.and.returnValue(of({ prl_daily: [], affr_daily: [] }));

    await TestBed.configureTestingModule({
      imports: [DashboardComponent, NoopAnimationsModule],
      providers: [
        FilterStateService,
        { provide: EnergyDataService, useValue: spy },
        provideHttpClient(),
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    dataSpy = TestBed.inject(EnergyDataService) as jasmine.SpyObj<EnergyDataService>;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load PRL data on init', () => {
    expect(dataSpy.getPrlData).toHaveBeenCalled();
  });

  it('should load statistics on init', () => {
    expect(dataSpy.getStatistics).toHaveBeenCalled();
  });

  it('should have default filter from service', () => {
    expect(component.filter.dataSource).toBe('api');
  });
});
