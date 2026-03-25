import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { RackDetail, RacksService } from '../../core/services/racks.service';

@Component({
  selector: 'app-rack-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './rack-detail.component.html',
})
export class RackDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private racksService = inject(RacksService);

  rackDetail: RackDetail | null = null;
  loading = true;
  error = '';

  ngOnInit(): void {
    const zone = this.route.snapshot.paramMap.get('zone');
    const rack = this.route.snapshot.paramMap.get('rack');

    if (!zone || !rack) {
      this.error = 'Parámetros inválidos';
      this.loading = false;
      return;
    }

    this.racksService.getRackDetail(zone, rack).subscribe({
      next: (data) => {
        this.rackDetail = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el detalle del rack';
        this.loading = false;
      },
    });
  }
}