import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-add-stock',
  templateUrl: './add-stock.component.html',
  styleUrls: ['./add-stock.component.css']
})
export class AddStockComponent implements OnInit {
  stockForm: FormGroup;
  companyName: string | null = '';
  companyId: string | null = '';
  tickerSymbol: string = '';
  formErrors: { [key: string]: string[] } = {};

  constructor(private fb: FormBuilder, private http: HttpClient) {
    this.companyName = localStorage.getItem('company_name'); // Get the company name from local storage
    this.companyId = localStorage.getItem('company_id'); // Get the company ID from local storage

    // Generate the ticker symbol from the company name
    this.tickerSymbol = this.companyName ? this.generateTickerSymbol(this.companyName) : '';

    this.stockForm = this.fb.group({
      ticker_symbol: [{ value: this.tickerSymbol, disabled: true }, Validators.required],
      total_shares: [0, [Validators.required, Validators.min(1)]],
      current_price: [0, [Validators.required, Validators.min(0.01)]],
      available_shares: [0, [Validators.required, Validators.min(1)]],
      max_trader_buy_limit: [0, [Validators.required, Validators.min(1)]],
    });
  }

  ngOnInit(): void {}

  /**
   * Generates a meaningful ticker symbol by taking the first letter of each word in the company name.
   * If the result is longer than three characters, trims it to three.
   */
  generateTickerSymbol(companyName: string): string {
    const words = companyName.split(/\s+/); // Split the company name by spaces
    let ticker = words.map(word => word[0].toUpperCase()).join(''); // Take the first letter of each word and join them
    return ticker.slice(0, 3); // Limit to three characters if longer
  }

  onSubmit(): void {
    if (this.stockForm.valid) {
      const payload = {
        company: this.companyId, // Use the company ID for submission
        ticker_symbol: this.tickerSymbol,
        total_shares: this.stockForm.value.total_shares,
        current_price: this.stockForm.value.current_price,
        available_shares: this.stockForm.value.available_shares,
        max_trader_buy_limit: this.stockForm.value.max_trader_buy_limit,
      };

      this.http.post('http://localhost:8000/api/stocks/stocks/', payload).subscribe(
        (response) => {
          alert('Stock added successfully!');
          this.stockForm.reset();
          this.formErrors = {}; // Clear any existing errors
        },
        (error) => {
          if (error.status === 400 && error.error) {
            this.formErrors = error.error; // Assign backend validation errors
          } else {
            alert('An unexpected error occurred. Please try again.');
          }
        }
      );
    }
  }

  /**
   * Returns the error message for a specific form field.
   * @param field The form field name
   * @returns The error message string
   */
  getErrorMessage(field: string): string | null {
    if (this.formErrors[field] && this.formErrors[field].length > 0) {
      return this.formErrors[field][0]; // Return the first error message
    }
    return null;
  }
}
