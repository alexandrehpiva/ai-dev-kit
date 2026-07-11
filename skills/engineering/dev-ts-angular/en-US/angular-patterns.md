# angular-patterns — Angular v17+ canonical patterns

## Version detection (always run first)

```bash
cat package.json | grep '"@angular/core"'
```

---

## Dependency injection — `inject()` only

```typescript
// Good
export class UsersPageComponent {
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
}

// Bad — constructor injection
export class UsersPageComponent {
  constructor(private userService: UserService, private router: Router) {}
}
```

---

## Block control flow (≥ v17)

```html
<!-- Good -->
@if (isLoading()) {
  <app-spinner />
} @else {
  @for (item of items(); track item.id) {
    <app-item [item]="item" />
  } @empty {
    <p>No items found.</p>
  }
}

<!-- Bad -->
<ng-container *ngIf="isLoading$ | async; else list">
<div *ngFor="let item of items; trackBy: trackById">
```

---

## Standalone components — no NgModules

```typescript
// Good
@Component({
  selector: 'app-example',
  standalone: true,
  imports: [RouterModule, ButtonComponent],
  templateUrl: './example.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExampleComponent {}

// Bad
@NgModule({ declarations: [ExampleComponent], exports: [ExampleComponent] })
export class ExampleModule {}
```

---

## Signals for reactive state

```typescript
// Good
readonly count = signal(0);
readonly doubled = computed(() => this.count() * 2);
readonly items = signal<Item[]>([]);

// Bad — BehaviorSubject for component state
private count$ = new BehaviorSubject(0);
readonly doubled$ = this.count$.pipe(map(n => n * 2));
```

---

## `effect()` — no `allowSignalWrites`

```typescript
// Good — writes are allowed by default since v18
effect(() => {
  this.derived.set(this.source() * 2);
});

// Bad — deprecated flag, do not use
effect(() => { ... }, { allowSignalWrites: true });
```

---

## Signal Forms — `@angular/forms/signals`

```typescript
import { form, FormField } from '@angular/forms/signals';

// Good
readonly loginForm = form({
  email: FormField.required(''),
  password: FormField.required(''),
});

// Bad — never use these directly for forms
import { FormBuilder, FormGroup, FormControl } from '@angular/forms';
```

Template binding with a shared UI library that supports Signal Forms:
```html
<!-- Good -->
<app-input [formField]="loginForm.controls.email" />

<!-- Bad -->
<app-input [formControl]="loginForm.controls.email" />
<app-input [(ngModel)]="email" />
```

---

## Smart vs. Dumb components

```typescript
// Good — Dumb: pure inputs/outputs, no services
@Component({ selector: 'app-user-card', standalone: true })
export class UserCardComponent {
  readonly user = input.required<User>();
  readonly select = output<User>();
}

// Good — Smart: owns services, state, routing
@Component({ selector: 'app-users-page', standalone: true })
export class UsersPageComponent {
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);

  readonly users = this.userService.users; // signal

  onSelect(user: User): void {
    void this.router.navigate(['/users', user.id]);
  }
}

// Bad — Dumb component injecting a service
@Component({ selector: 'app-user-card', standalone: true })
export class UserCardComponent {
  private readonly router = inject(Router); // ← wrong layer
}
```

---

## Typed interfaces and discriminated unions

```typescript
// Good — named interface
interface UserProfile {
  id: string;
  email: string;
  role: 'admin' | 'viewer';
}

// Good — discriminated union
type ApiState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };

function handleState<T>(state: ApiState<T>): string {
  switch (state.status) {
    case 'loading': return 'Loading…';
    case 'success': return `${state.data}`;
    case 'error':   return state.message;
    default: return assertNever(state);
  }
}

// Bad — all-optional flat interface hides variants
interface ApiState<T> {
  loading?: boolean;
  data?: T;
  error?: string;
}
```

---

## Strict typing — never `any`

`HttpClient.get()` returns `Observable<T>` — never `await` it directly. Keep HTTP calls in a service; consume via `toSignal()` at the component boundary.

```typescript
// Good — service exposes a typed Observable
@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>('/users');
  }
}

// Good — smart component converts to signal
@Component({ ... })
export class UsersPageComponent {
  private readonly userService = inject(UserService);

  readonly users = toSignal(this.userService.getUsers(), { initialValue: [] });
}

// Bad — any leaks through, and HttpClient does not belong in a component
export class UsersPageComponent {
  private readonly http = inject(HttpClient);

  async loadUsers(): Promise<void> {
    const response: any = await this.http.get('/users'); // two mistakes at once
  }
}
```

---

## Declarative pipelines — flatten nesting

```typescript
// Good — declarative, readable
readonly activeAdminEmails = computed(() =>
  this.users()
    .filter(u => u.isActive && u.role === 'admin')
    .map(u => u.email),
);

// Bad — imperative nesting
readonly activeAdminEmails = computed(() => {
  const result: string[] = [];
  for (const u of this.users()) {
    if (u.isActive) {
      if (u.role === 'admin') {
        result.push(u.email);
      }
    }
  }
  return result;
});
```

---

## `input()` / `output()` (≥ v17.3)

```typescript
// Good
readonly label = input.required<string>();
readonly disabled = input(false);
readonly clicked = output<void>();

// Bad
@Input() label!: string;
@Output() clicked = new EventEmitter<void>();
```

---

## No template method calls — use `computed()` signals

Calling a class method directly from a template re-executes it on **every change detection cycle**, bypassing Angular's memoization entirely. Every non-trivial derivation must live in a `computed()` signal.

**The rule:** a call expression `foo()` or `foo(arg)` in a template is only valid if `foo` is declared as `signal(...)`, `computed(...)`, `input(...)`, or a service's signal accessor. Everything else is a violation.

```html
<!-- Bad — method calls; re-run every CD cycle -->
<h2>{{ getTitle(i) }}</h2>
<button [disabled]="isDisabled(item)">…</button>
@for (b of buyers(); track b.id) {
  <span>{{ formatLabel(i) }}</span>
}

<!-- Good — computed signal arrays; derived once, read by index -->
<h2>{{ titles()[i] }}</h2>
<button [disabled]="!canAdd()">…</button>  <!-- canAdd is a computed() -->
@for (b of buyers(); track b.id) {
  <span>{{ labels()[i] }}</span>
}
```

```typescript
// Bad — method on the class
protected getTitle(i: number): string {
  return i === 0 ? 'Primary' : `Participant ${i}`;
}

// Good — computed array indexed by loop position
protected readonly titles = computed(() =>
  this.participants.buyers().map((_, i) =>
    i === 0 ? 'Primary' : `Participant ${i}`,
  ),
);
```

**How to spot violations during review:** grep template files for any `\w\+(` that is not preceded by `(`, `=`, or `;` (i.e., event bindings are exempt — `(click)="handler($event)"` is fine). For each hit, verify the callee is a `signal`/`computed`/`input` declaration, not a plain class method.

**Signal reads look identical but are fine:**
```html
{{ mySignal() }}               <!-- signal read — fine -->
{{ service.count() }}          <!-- service signal accessor — fine -->
{{ items().length }}           <!-- chained property on signal — fine -->
{{ formatDate(item.date) }}    <!-- plain method with arg — VIOLATION -->
```

**Event bindings are exempt** — `(click)="doSomething()"` is correct; the handler runs on user action, not on every CD cycle.

---

## Anti-patterns checklist

| Anti-pattern | Correct alternative |
|---|---|
| `*ngIf` / `*ngFor` | `@if` / `@for` |
| `@NgModule` | Standalone `@Component` / `@Pipe` / `@Directive` |
| Constructor DI | `inject()` |
| `FormBuilder` / `FormGroup` | Signal Forms (`form()`, `FormField`) |
| `BehaviorSubject` in component | `signal()` |
| `any` | Proper interface or generic |
| `!` non-null assertion | Narrowing or type redesign |
| Inline `{ prop: Type }` shapes | Named `interface` |
| `allowSignalWrites: true` | Remove — writes are default |
| `@Input()` / `@Output()` | `input()` / `output()` |
| Method calls in templates (`foo(arg)`, `getX(i)`) | `computed()` signal array indexed by loop position |
