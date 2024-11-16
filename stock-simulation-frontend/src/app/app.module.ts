import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms'; 
import { HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

// Angular Material Components
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';  // Add this

import { ToastrModule } from 'ngx-toastr';
import { AppRoutingModule } from './app-routing.module';

// Components
import { AppComponent } from './app.component';
import { AuthLoginComponent } from './components/auth-login/auth-login.component';
import { AuthRegisterComponent } from './components/auth-register/auth-register.component';
import { HomeComponent } from './components/home/home.component';
import { UserListComponent } from './components/user-list.component.ts/user-list.component.ts.component';
import { MatTableModule } from '@angular/material/table';

@NgModule({
  declarations: [
    AppComponent,
    AuthLoginComponent,
    AuthRegisterComponent,
    HomeComponent,
    UserListComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    ToastrModule.forRoot({
      positionClass: 'toast-top-right',
      timeOut: 3000,
      closeButton: true,
      preventDuplicates: true
    }),
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    BrowserAnimationsModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatSelectModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule, // Add this module
    AppRoutingModule,
    MatTableModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
