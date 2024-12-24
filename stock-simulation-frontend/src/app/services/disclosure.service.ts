import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DisclosureService {
  private BASE_URL = 'http://127.0.0.1:8000/api';  // Adjust to your real endpoint

  constructor(private http: HttpClient) {}

  uploadDisclosure(formData: FormData): Observable<any> {
    // If your endpoint is /disclosures/ using the ViewSet
    return this.http.post(`${this.BASE_URL}/disclosures/`, formData);
  }
}
