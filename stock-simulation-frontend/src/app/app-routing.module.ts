import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthLoginComponent } from './components/auth-login/auth-login.component';
import { AuthRegisterComponent } from './components/auth-register/auth-register.component';
import { HomeComponent } from './components/home/home.component';
import { UserListComponent } from './components/user-list.component.ts/user-list.component.ts.component';
import { OrdersComponent } from './components/orders/orders.component';
import { AuthGuard } from './auth.guard';
import { LayoutComponent } from './layout/layout.component';
import { PublishStockComponent } from './components/publish-stock/publish-stock.component';
import { OtpVerificationComponent } from './components/otp-verification/otp-verification.component';

// const routes: Routes = [
//   { path: 'login', component: AuthLoginComponent },
//   { path: 'register', component: AuthRegisterComponent },
//   { path: 'home', component: HomeComponent },  // Add the home route
//   { path: '', redirectTo: '/login', pathMatch: 'full' } , // Default redirect to login
//   { path: 'users', component: UserListComponent },
//  // { path: '**', redirectTo: '/login' }, // Wildcard route to redirect invalid URLs to login
//   { path: 'orders', component: OrdersComponent },
//   { path: '**', redirectTo: '/orders' }, // Default to orders for testing
// ];
const routes: Routes = [
  { path: 'login', component: AuthLoginComponent }, // Public route
  { path: 'register', component: AuthRegisterComponent }, // Public route
  {
    path: '',
    component: LayoutComponent,
    canActivate: [AuthGuard], // Protect with AuthGuard
    children: [
      { path: 'home', component: HomeComponent }, // Home page content only
      { path: 'orders', component: OrdersComponent },
      { path: 'publish-stock', component: PublishStockComponent },
      { path: 'otp-verification', component: OtpVerificationComponent },
     // { path: 'kyc-pending', component: KycPendingComponent }, // Page after success
    ],
  },
  { path: '**', redirectTo: '/login' }, // Redirect unknown routes to login
];


@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
