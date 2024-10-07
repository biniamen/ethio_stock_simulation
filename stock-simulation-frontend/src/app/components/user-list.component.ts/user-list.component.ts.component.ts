import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { MatTableDataSource } from '@angular/material/table';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.ts.component.html',
  styleUrls: ['./user-list.component.ts.component.css']
})
export class UserListComponent implements OnInit {
  displayedColumns: string[] = ['username', 'email', 'role', 'kyc_verified', 'kyc_document', 'actions'];
  dataSource!: MatTableDataSource<any>;

  constructor(private authService: AuthService, private toastr: ToastrService) {}

  ngOnInit() {
    this.fetchUsers();
  }

  fetchUsers() {
    this.authService.listUsers().subscribe(
      data => {
        this.dataSource = new MatTableDataSource(data);
      },
      error => {
        console.error('Error fetching users', error);
        this.toastr.error('Failed to fetch users', 'Error');
      }
    );
  }

  approveKyc(userId: number) {
    this.authService.updateKycStatus(userId, 'approve').subscribe(
      response => {
        this.toastr.success('KYC approved', 'Success');
        this.fetchUsers();  // Refresh the list
      },
      error => {
        console.error('Error approving KYC', error);
        this.toastr.error('Failed to approve KYC', 'Error');
      }
    );
  }

  rejectKyc(userId: number) {
    this.authService.updateKycStatus(userId, 'reject').subscribe(
      response => {
        this.toastr.success('KYC rejected', 'Success');
        this.fetchUsers();  // Refresh the list
      },
      error => {
        console.error('Error rejecting KYC', error);
        this.toastr.error('Failed to reject KYC', 'Error');
      }
    );
  }
}
