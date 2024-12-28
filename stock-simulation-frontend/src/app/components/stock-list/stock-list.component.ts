import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';

@Component({
  selector: 'app-stock-list',
  templateUrl: './stock-list.component.html',
  styleUrls: ['./stock-list.component.css'],
})
export class StockListComponent implements OnInit {
  @ViewChild('buyModal') buyModal!: TemplateRef<any>;
  @ViewChild('disclosureModal') disclosureModal!: TemplateRef<any>;
  @ViewChild(MatPaginator, { static: false }) paginator!: MatPaginator;
  @ViewChild(MatSort, { static: false }) sort!: MatSort;

  stocks: any[] = [];
  filteredStocks: any[] = [];
  selectedStock: any = null;
  disclosures: any[] = [];
  disclosureDataSource = new MatTableDataSource<any>();
  displayedColumns: string[] = ['id', 'type', 'year', 'description', 'file'];
  token: string | null = null;
  quantity: string = '';
  searchText: string = '';

  constructor(private http: HttpClient, public dialog: MatDialog) {}

  ngOnInit(): void {
    this.token = localStorage.getItem('access_token');
    if (!this.token) {
      alert('You must log in to access this page.');
      return;
    }
    this.fetchStocks();
  }

  ngAfterViewInit(): void {
    // Ensure the paginator is attached after the view is initialized
    this.disclosureDataSource.paginator = this.paginator;
    this.disclosureDataSource.sort = this.sort;
  }

  fetchStocks(): void {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http.get<any[]>('http://127.0.0.1:8000/api/stocks/stocks/', { headers }).subscribe({
      next: (data) => {
        this.stocks = data.filter((stock) => stock.available_shares > 0);
        this.filteredStocks = [...this.stocks];
      },
      error: (err) => {
        console.error('Error fetching stocks:', err);
        if (err.status === 401) {
          alert('Authentication failed. Please log in again.');
        } else if (err.status === 0) {
          alert('Cannot connect to the server. Please check if the backend is running and CORS is configured.');
        } else {
          alert(`Unexpected error: ${err.message}`);
        }
      },
    });
  }

  openBuyModal(stock: any): void {
    this.selectedStock = stock;
    this.quantity = '';
    this.dialog.open(this.buyModal, { width: '500px', height: 'auto' });
  }

  placeOrder(): void {
    const quantityValue = parseInt(this.quantity, 10);

    if (isNaN(quantityValue) || quantityValue <= 0) {
      alert('Please enter a valid quantity.');
      return;
    }

    if (!this.selectedStock) {
      alert('No stock selected.');
      return;
    }

    const userId = localStorage.getItem('user_id');
    if (!userId) {
      alert('User not logged in. Please log in first.');
      return;
    }

    const payload = {
      user_id: userId,
      stock_id: this.selectedStock.id,
      quantity: quantityValue,
    };

    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    });

    this.http.post('http://127.0.0.1:8000/api/stocks/direct_buy/', payload, { headers }).subscribe({
      next: (response: any) => {
        alert(`Order placed successfully! Total cost: ${response.total_cost}`);
        this.dialog.closeAll();
        this.fetchStocks();
      },
      error: (err) => {
        console.error('Error placing order:', err);
        if (err.status === 401) {
          alert('Authentication failed. Please log in again.');
        } else {
          alert(err.error.detail || 'Failed to place the order.');
        }
      },
    });
  }

  openDisclosureModal(companyId: number): void {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http
      .get<any[]>(`http://127.0.0.1:8000/api/stocks/company/${companyId}/disclosures/`, { headers })
      .subscribe({
        next: (data) => {
          this.disclosures = data;
          this.disclosureDataSource = new MatTableDataSource(this.disclosures);
          this.disclosureDataSource.paginator = this.paginator;
          this.disclosureDataSource.sort = this.sort;
          this.dialog.open(this.disclosureModal, { width: '800px', height: 'auto' });
        },
        error: (err) => {
          console.error('Error fetching disclosures:', err);
          alert('Failed to fetch disclosures.');
        },
      });
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.disclosureDataSource.filter = filterValue;

    if (this.disclosureDataSource.paginator) {
      this.disclosureDataSource.paginator.firstPage();
    }
  }

  hoverEffect(enable: boolean, stockId: number): void {
    const card = document.querySelector(`#stock-card-${stockId}`) as HTMLElement;
    if (card) {
      card.style.boxShadow = enable ? '0px 4px 10px rgba(0, 0, 0, 0.2)' : 'none';
      card.style.transform = enable ? 'scale(1.05)' : 'scale(1)';
      card.style.transition = 'transform 0.3s, box-shadow 0.3s';
    }
  }

  filterStocks(): void {
    this.filteredStocks = this.stocks.filter((stock) =>
      stock.ticker_symbol.toLowerCase().includes(this.searchText.toLowerCase())
    );
  }

  closeModal(): void {
    this.dialog.closeAll();
  }
}
