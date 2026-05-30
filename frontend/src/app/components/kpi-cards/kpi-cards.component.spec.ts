import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { KpiCardsComponent } from './kpi-cards.component';
import { Statistics } from '../../models/energy-data.model';

describe('KpiCardsComponent', () => {
  let component: KpiCardsComponent;
  let fixture: ComponentFixture<KpiCardsComponent>;

  const mockStats: Statistics = {
    prl: { mean_positive: 1.23, mean_negative: -0.89, max_positive: 45.6, max_negative: -52.1, std_positive: 18.9, total_intervals: 672 },
    affr: { mean_activation: 52.3, max_activation: 612.4, total_activated_mwh: 8790.5, activation_rate: 67.8 },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [KpiCardsComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(KpiCardsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display 4 cards when both showPrl and showAffr are true', () => {
    component.statistics = mockStats;
    component.showPrl = true;
    component.showAffr = true;
    component.ngOnChanges();
    expect(component.cards.length).toBe(4);
  });

  it('should display 2 cards when only showPrl is true', () => {
    component.statistics = mockStats;
    component.showPrl = true;
    component.showAffr = false;
    component.ngOnChanges();
    expect(component.cards.length).toBe(2);
  });

  it('should format PRL mean value correctly', () => {
    component.statistics = mockStats;
    component.ngOnChanges();
    expect(component.cards[0].value).toBe('1.2 MW');
  });

  it('should show empty cards when statistics is null', () => {
    component.statistics = null;
    component.ngOnChanges();
    expect(component.cards.length).toBe(0);
  });
});
