import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(private router: Router) {}

  canActivate(): boolean {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('role'); // Assume the role is stored in localStorage
    if (token && role === 'trader') {
      return true;
    } else {
      this.router.navigate(['/login']); // Redirect if not a trader
      return false;
    }
  }
}
