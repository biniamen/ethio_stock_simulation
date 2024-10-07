import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000/api/users/';

  constructor(private http: HttpClient) { }

  // Handle user registration
  register(user: FormData): Observable<any> {
    return this.http.post(this.apiUrl + 'register/', user);
  }

  // Handle user login
  login(credentials: any): Observable<any> {
    return this.http.post(this.apiUrl + 'login/', credentials);
  }

  // List all registered users (Regulator only)
  listUsers(): Observable<any> {
    return this.http.get(this.apiUrl);
  }

  // Approve or reject KYC status (Regulator only)
  updateKycStatus(userId: number, action: string): Observable<any> {
    return this.http.post(`${this.apiUrl}${userId}/kyc/`, { action });
  }
}
