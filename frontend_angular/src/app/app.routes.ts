import { Routes } from '@angular/router';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { RackDetailComponent } from './features/rack-detail/rack-detail.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'racks/:zone/:rack', component: RackDetailComponent },
];