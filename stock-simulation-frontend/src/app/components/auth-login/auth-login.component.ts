import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-auth-login',
  templateUrl: './auth-login.component.html',
  styleUrls: ['./auth-login.component.css']
})
export class AuthLoginComponent implements OnInit {
  loginUser = { username: '', password: '' };

  constructor(private authService: AuthService, private toastr: ToastrService, private router: Router) {}

  ngOnInit(): void {
    // Redirect if already logged in
    if (localStorage.getItem('access_token')) {
      this.router.navigate(['/home']);
    }
  }

  onLogin() {
    this.authService.login(this.loginUser).subscribe(
      response => {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        localStorage.setItem('username', response.username);
        localStorage.setItem('kyc_status', response.kyc_verified);
        localStorage.setItem('role', response.role);

        this.toastr.success('Login successful!', 'Success');
        this.router.navigate(['/home']);
      },
      error => {
        this.toastr.error('Login failed. Check your credentials.', 'Error');
      }
    );
  }
}
