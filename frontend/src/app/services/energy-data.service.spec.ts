import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { EnergyDataService } from './energy-data.service';
import { FilterState, PrlResponse, Statistics, UploadResponse } from '../models/energy-data.model';

describe('EnergyDataService', () => {
  let service: EnergyDataService;
  let http: HttpTestingController;

  const mockFilter: FilterState = {
    dataSource: 'demo',
    startDate: '2024-06-01',
    endDate: '2024-06-07',
    showPrl: true,
    showAffr: true,
    showGesamt: true,
    tsos: { _50hertz: false, amprion: false, tennet: false, transnetbw: false },
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EnergyDataService],
    });
    service = TestBed.inject(EnergyDataService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch PRL data via GET /api/energy/prl', () => {
    service.getPrlData(mockFilter).subscribe((res) => {
      expect(res.data.length).toBe(1);
      expect(res.metadata.source).toBe('demo');
    });

    const req = http.expectOne((r) => r.url.includes('/api/energy/prl'));
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('source')).toBe('demo');
    req.flush({ data: [{ timestamp: '2024-06-01T00:00:00', deutschland_positiv_mw: 12.5, deutschland_negativ_mw: -8.3 }], metadata: { interval_count: 1, source: 'demo' } });
  });

  it('should fetch aFRR data via GET /api/energy/affr', () => {
    service.getAffrData(mockFilter).subscribe((res) => {
      expect(res.data.length).toBe(1);
    });

    const req = http.expectOne((r) => r.url.includes('/api/energy/affr'));
    expect(req.request.method).toBe('GET');
    req.flush({ data: [{ timestamp: '2024-06-01T00:00:00', deutschland_positiv_mw: 100, deutschland_negativ_mw: 0 }], metadata: { interval_count: 1, source: 'demo' } });
  });

  it('should fetch statistics via GET /api/energy/statistics', () => {
    service.getStatistics(mockFilter).subscribe((res) => {
      expect(res.prl.mean_positive).toBeDefined();
    });

    const req = http.expectOne((r) => r.url.includes('/api/energy/statistics'));
    expect(req.request.params.get('start')).toBe('2024-06-01');
    req.flush({ prl: { mean_positive: 1.23 }, affr: { mean_activation: 50 } } as Statistics);
  });

  it('should upload CSV via POST /api/energy/upload', () => {
    const file = new File(['a,b\n1,2'], 'test.csv', { type: 'text/csv' });
    service.uploadCsv(file, 'prl').subscribe((res) => {
      expect(res.success).toBeTrue();
    });

    const req = http.expectOne((r) => r.url.includes('/api/energy/upload') && r.params.get('type') === 'prl');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBeTrue();
    req.flush({ success: true, rows: 1, columns: ['a', 'b'], preview: [] } as UploadResponse);
  });

  it('should handle HTTP errors', () => {
    service.getPrlData(mockFilter).subscribe({ error: (err) => expect(err.status).toBe(500) });
    const req = http.expectOne((r) => r.url.includes('/api/energy/prl'));
    req.flush('Server Error', { status: 500, statusText: 'Error' });
  });
});
