import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { interval, Subject, takeUntil } from 'rxjs';
import { RackSummary, RacksService } from '../../core/services/racks.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit, OnDestroy {
  private racksService = inject(RacksService);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  racks: RackSummary[] = [];
  loading = true;
  error = '';

  ngOnInit(): void {
    this.loadRacks();

    interval(5000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.loadRacks();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadRacks(): void {
    this.racksService.getRacks().subscribe({
      next: (data) => {
        this.racks = data.sort((a, b) => {
          if (a.zone === b.zone) {
            return a.rack.localeCompare(b.rack);
          }
          return a.zone.localeCompare(b.zone);
        });

        this.error = '';
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el estado de los racks';
        this.loading = false;
      },
    });
  }

  goToRack(rack: RackSummary): void {
    this.router.navigate(['/racks', rack.zone, rack.rack]);
  }
}