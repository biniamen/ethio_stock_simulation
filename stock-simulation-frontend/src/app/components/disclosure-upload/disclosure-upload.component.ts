import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { DisclosureService } from 'src/app/services/disclosure.service';

@Component({
  selector: 'app-disclosure-upload',
  templateUrl: './disclosure-upload.component.html',
  styleUrls: ['./disclosure-upload.component.css']
})
export class DisclosureUploadComponent implements OnInit {
  disclosureForm!: FormGroup;
  selectedFile: File | null = null;

  // Replace or adjust these to match your actual model choices
  disclosureTypes = [
    'Financial Statement',
    'Annual Report',
    'Material Event',
    'Quarterly Report'
  ];

  constructor(
    private fb: FormBuilder,
    private disclosureService: DisclosureService
  ) {}

  ngOnInit(): void {
    // Suppose you stored the logged-in company's ID in localStorage under key 'companyId'
    const companyId = localStorage.getItem('companyId');

    this.disclosureForm = this.fb.group({
      company: [companyId, Validators.required],
      type: [null, Validators.required],
      year: [null, [Validators.required, Validators.min(1900)]],
      description: [null]
    });
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0] || null;
  }

  onSubmit(): void {
    if (!this.disclosureForm.valid) {
      alert('Please fill in all required fields.');
      return;
    }
    if (!this.selectedFile) {
      alert('Please select a file.');
      return;
    }

    const formData = new FormData();
    // Make sure your serializer expects "company" as an integer
    formData.append('company', this.disclosureForm.value.company);
    formData.append('type', this.disclosureForm.value.type);
    formData.append('year', this.disclosureForm.value.year);
    formData.append('description', this.disclosureForm.value.description || '');
    formData.append('file', this.selectedFile);

    this.disclosureService.uploadDisclosure(formData).subscribe({
      next: (res) => {
        console.log('Uploaded Successfully:', res);
        alert('Disclosure uploaded successfully!');
        this.disclosureForm.reset();
        this.selectedFile = null;
      },
      error: (err) => {
        console.error('Error uploading disclosure:', err);
        alert('Failed to upload disclosure.');
      }
    });
  }
}
