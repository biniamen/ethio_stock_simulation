import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.css'],
})
export class LayoutComponent implements OnInit {
  username: string | null = '';
  kycStatus: string | null = '';
  role: string | null = '';
  isLoggedIn: boolean = false;

  constructor(private router: Router) {}

  ngOnInit(): void {
    const token = localStorage.getItem('access_token');
    this.isLoggedIn = !!token;

    if (this.isLoggedIn) {
      this.username = localStorage.getItem('username');
      this.kycStatus = localStorage.getItem('kyc_status');
      this.role = localStorage.getItem('role');
    } else {
      this.router.navigate(['/login']);
    }
  }

  onLogout(): void {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
