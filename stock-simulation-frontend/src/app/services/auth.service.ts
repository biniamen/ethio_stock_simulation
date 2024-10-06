import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000/api/users/';

  constructor(private http: HttpClient) { }

  register(user: FormData): Observable<any> {
    return this.http.post(this.apiUrl + 'register/', user);
  }

  login(credentials: any): Observable<any> {
    return this.http.post(this.apiUrl + 'login/', credentials);
  }
}
