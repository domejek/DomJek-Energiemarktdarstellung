import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { Statistics } from '../../models/energy-data.model';

@Component({
  selector: 'app-kpi-cards',
  standalone: true,
  imports: [CommonModule, MatCardModule],
  templateUrl: './kpi-cards.component.html',
  styleUrl: './kpi-cards.component.scss',
})
export class KpiCardsComponent implements OnChanges {
  @Input() statistics: Statistics | null = null;
  @Input() showPrl = true;
  @Input() showAffr = true;

  cards: Array<{ label: string; value: string; delta: string }> = [];

  ngOnChanges(): void {
    this.buildCards();
  }

  private buildCards(): void {
    this.cards = [];
    const s = this.statistics;
    if (!s) return;

    if (this.showPrl) {
      this.cards.push({
        label: 'PRL Ø Positiv',
        value: `${s.prl.mean_positive.toFixed(1)} MW`,
        delta: `${s.prl.std_positive.toFixed(1)} MW σ`,
      });
      this.cards.push({
        label: 'PRL Maximum',
        value: `${s.prl.max_positive.toFixed(1)} MW`,
        delta: `${s.prl.max_negative.toFixed(1)} MW (min)`,
      });
    }

    if (this.showAffr) {
      this.cards.push({
        label: 'aFRR Ø Aktivierung',
        value: `${s.affr.mean_activation.toFixed(1)} MW`,
        delta: `${s.affr.activation_rate.toFixed(1)}% aktiv`,
      });
      this.cards.push({
        label: 'Gesamt Energie',
        value: `${s.affr.total_activated_mwh.toFixed(0)} MWh`,
        delta: `${s.affr.max_activation.toFixed(0)} MW (max)`,
      });
    }
  }
}
