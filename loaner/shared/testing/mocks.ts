// Copyright 2018 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {NgModule} from '@angular/core';
import {ComponentFixtureAutoDetect} from '@angular/core/testing';
import {Observable, of} from 'rxjs';

import {Damaged} from '../components/damaged';
import {Extend} from '../components/extend';
import {GuestMode} from '../components/guest';
import {Lost} from '../components/lost';
import {Unenroll} from '../components/unenroll';

export abstract class DeviceActionsDialogService {
  openDialog() {}

  finished() {}

  close() {}
}

export class DamagedMock extends DeviceActionsDialogService {
  get onDamaged(): Observable<string> {
    return of('damagedReason');
  }
}

export class ExtendMock extends DeviceActionsDialogService {
  get onExtended(): Observable<string> {
    return of('newDate');
  }
}

export class GuestModeMock extends DeviceActionsDialogService {
  get onGuestModeEnabled(): Observable<boolean> {
    return of(true);
  }
}

export class ResumeLoanMock extends DeviceActionsDialogService {
  get onLoanResumed(): Observable<boolean> {
    return of(true);
  }
}

export class LostMock extends DeviceActionsDialogService {
  get onLost(): Observable<boolean> {
    return of(true);
  }
}

export class UnenrollMock extends DeviceActionsDialogService {
  get onUnenroll(): Observable<boolean> {
    return of(true);
  }
}

@NgModule({
  providers: [
    {provide: ComponentFixtureAutoDetect, useValue: true},
    {provide: Damaged, useClass: DamagedMock},
    {provide: Extend, useClass: ExtendMock},
    {provide: GuestMode, useClass: GuestModeMock},
    {provide: Lost, useClass: LostMock},
    {provide: Unenroll, useClass: UnenrollMock},
  ],
})
export class SharedMocksModule {
}
