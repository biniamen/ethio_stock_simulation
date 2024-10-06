import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-auth-register',
  templateUrl: './auth-register.component.html',
  styleUrls: ['./auth-register.component.css']
})
export class AuthRegisterComponent {
  user = { username: '', email: '', password: '', role: 'trader' };
  selectedFile: File | null = null;

  constructor(private authService: AuthService, private toastr: ToastrService) { }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  onRegister() {
    const formData = new FormData();
    formData.append('username', this.user.username);
    formData.append('email', this.user.email);
    formData.append('password', this.user.password);
    formData.append('role', this.user.role);
    if (this.selectedFile) {
      formData.append('kyc_document', this.selectedFile);
    }

    this.authService.register(formData).subscribe(
      response => {
        console.log('User registered successfully', response);
        this.toastr.success('Registration successful!', 'Success');
        
        // Reset the form after successful registration
        this.user = { username: '', email: '', password: '', role: 'trader' };
        this.selectedFile = null;

        // Reset the file input element
        const fileInput = document.getElementById('kycFile') as HTMLInputElement;
        if (fileInput) {
          fileInput.value = '';
        }
      },
      error => {
        console.error('Error registering user', error);
        this.toastr.error('Registration failed. Please try again.', 'Error');
      }
    );
  }
}
