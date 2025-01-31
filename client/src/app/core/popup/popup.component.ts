import { Component, Inject } from '@angular/core';
import { MAT_SNACK_BAR_DATA } from '@angular/material/snack-bar';

import { SnackBarTypes, SnackBarTypesT } from '@core/services/common/popup.config';
@Component({
  selector: 'wb-popup',
  templateUrl: 'popup.component.html',
  styleUrls: ['popup.component.scss'],
})
export class PopupComponent {
  public snackBarTypes = SnackBarTypes;
  constructor(@Inject(MAT_SNACK_BAR_DATA) public data: { message: string; type: SnackBarTypesT }) {}
}
