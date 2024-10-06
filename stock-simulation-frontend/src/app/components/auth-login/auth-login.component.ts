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
        console.log('User logged in successfully', response);
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);

        // Assuming response contains username and kyc_status
        localStorage.setItem('username', response.username);
        localStorage.setItem('kyc_status', response.kyc_status);

        this.toastr.success('Login successful!', 'Success');

        // Redirect to the home page after successful login
        this.router.navigate(['/home']);
      },
      error => {
        console.error('Error logging in', error);
        this.toastr.error('Login failed. Please check your credentials.', 'Error');
      }
    );
  }
}
