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
import { StockListComponent } from './components/stock-list/stock-list.component';
import { BidOrderComponent } from './components/bid-order/bid-order.component';
import { AddStockComponent } from './components/add-stock/add-stock.component';
import { DisclosureUploadComponent } from './components/disclosure-upload/disclosure-upload.component';

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
  { path: 'otp-verification', component: OtpVerificationComponent }, // Public route for OTP verification

  {
    path: '',
    component: LayoutComponent,
    canActivate: [AuthGuard], // Protect with AuthGuard
    children: [
      { path: 'home', component: HomeComponent }, // Home page content only
      { path: 'orders', component: OrdersComponent },
      { path: 'stocks', component: StockListComponent },
      { path: 'publish-stock', component: PublishStockComponent },
      { path: 'bid-order', component: BidOrderComponent },
      { path: 'add-stock', component: AddStockComponent },
      { path: 'upload-disclosure', component: DisclosureUploadComponent },

      // { path: 'otp-verification', component: OtpVerificationComponent },
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
