import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthLoginComponent } from './components/auth-login/auth-login.component';
import { AuthRegisterComponent } from './components/auth-register/auth-register.component';
import { HomeComponent } from './components/home/home.component';
import { UserListComponent } from './components/user-list.component.ts/user-list.component.ts.component';

const routes: Routes = [
  { path: 'login', component: AuthLoginComponent },
  { path: 'register', component: AuthRegisterComponent },
  { path: 'home', component: HomeComponent },  // Add the home route
  { path: '', redirectTo: '/login', pathMatch: 'full' } , // Default redirect to login
  { path: 'users', component: UserListComponent },

];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
