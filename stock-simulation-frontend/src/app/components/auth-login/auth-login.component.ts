import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';  // Import Router

@Component({
  selector: 'app-auth-login',
  templateUrl: './auth-login.component.html',
  styleUrls: ['./auth-login.component.css']
})
export class AuthLoginComponent {
  loginUser = { username: '', password: '' };

  constructor(private authService: AuthService, private toastr: ToastrService, private router: Router) { }

  onLogin() {
    this.authService.login(this.loginUser).subscribe(
      response => {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        localStorage.setItem('username', response.username);
        localStorage.setItem('kyc_status', response.kyc_status);
  
        this.toastr.success('Login successful!', 'Success');
        this.router.navigate(['/home']);
      },
      error => {
        console.error('Login error:', error);
  
        // Handle specific KYC verification error
        if (error.error && error.error.detail) {
          try {
            // Extract the error message manually
            const regex = /ErrorDetail\(string='(.*?)'/; // Regex to capture the error message
            const match = error.error.detail.match(regex);
  
            if (match && match[1]) {
              this.toastr.error(match[1], 'KYC Error'); // Display the extracted error message
            } else {
              this.toastr.error('An unknown error occurred during login.', 'Error');
            }
          } catch (e) {
            this.toastr.error('An unknown error occurred during login.', 'Error');
          }
        } else {
          this.toastr.error('Login failed. Check your credentials.', 'Error');
        }
      }
    );
  }
  
}
