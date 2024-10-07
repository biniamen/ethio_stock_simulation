import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-auth-register',
  templateUrl: './auth-register.component.html',
  styleUrls: ['./auth-register.component.css']
})
export class AuthRegisterComponent {
  // Define the form object
  user = { username: '', email: '', password: '', role: 'trader' };
  selectedFile: File | null = null;

  constructor(private authService: AuthService, private toastr: ToastrService) { }

  // Handle file selection for KYC document
  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  // Handle user registration form submission
  onRegister() {
    const formData = new FormData();
    formData.append('username', this.user.username);
    formData.append('email', this.user.email);
    formData.append('password', this.user.password);
    formData.append('role', this.user.role);

    // Append KYC document only if uploaded by the user
    if (this.selectedFile) {
      formData.append('kyc_document', this.selectedFile);
    }

    // Call authService to handle registration
    this.authService.register(formData).subscribe(
      response => {
        console.log('User registered successfully', response);
        this.toastr.success('Registration successful!', 'Success');
        
        // Reset form fields after successful registration
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
