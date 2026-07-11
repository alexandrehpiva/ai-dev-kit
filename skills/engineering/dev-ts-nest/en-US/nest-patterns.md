# nest-patterns — NestJS canonical patterns

## Version detection (always run first)

```bash
cat package.json | grep '"@nestjs/core"'
```

---

## Scaffolding — use the CLI, don't hand-roll

```bash
# Good — scaffold a full feature module, then adapt to house conventions
pnpm nest g resource leads

# Good — scaffold one artifact at a time
pnpm nest g module leads
pnpm nest g controller leads
pnpm nest g service leads

# Bad — hand-typing module/controller boilerplate from scratch
# (skips the CLI's correct decorators, imports, and spec skeleton)
```

---

## Module anatomy — feature-first

```
src/leads/
  leads.module.ts
  leads.controller.ts
  leads.service.ts
  leads.controller.spec.ts
  leads.service.spec.ts
  dto/save-lead-draft.dto.ts
```

```typescript
// Good
@Module({
  controllers: [LeadsController],
  providers: [LeadsService],
})
export class LeadsModule {}
```

---

## Dependency injection — constructor only

```typescript
// Good
@Injectable()
export class LeadsService {
  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {}
}

// Bad — manual instantiation, no DI
export class LeadsService {
  private readonly http = new HttpService();
}
```

### Request-scoped providers — pair the scope correctly

```typescript
// Good — REQUEST injection paired with REQUEST scope
@Injectable({ scope: Scope.REQUEST })
export class AuthService {
  constructor(@Inject(REQUEST) private readonly req: Request) {}
}

// Bad — injects REQUEST but declares DEFAULT (singleton) scope — a real bug, not a shortcut
@Injectable({ scope: Scope.DEFAULT })
export class AuthService {
  constructor(@Inject(REQUEST) req: Request) {}
}
```

---

## DTOs & validation

```typescript
// Good — class, decorated, nested validation
export class SaveLeadDraftDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @ValidateNested()
  @Type(() => AddressDto)
  address: AddressDto;
}

// Bad — response shape as a bare interface (no Swagger metadata, can't be decorated)
export interface LeadDraftResponseDto {
  id: string;
  name: string;
}
```

Wire the global pipe once, in `main.ts`:
```typescript
app.useGlobalPipes(new ValidationPipe({ transform: true, whitelist: true }));
```

---

## Env config — `ConfigService`, never `process.env`

```typescript
// Good
@Injectable()
export class LeadsService {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('MS_LEADS_URL') ?? '';
  }
}

// Bad — direct process.env read inside a service
export class LeadsService {
  private readonly baseUrl = process.env['MS_LEADS_URL'] ?? '';
}
```

Validate the shape once, at bootstrap:
```typescript
export function validateEnv(config: Record<string, unknown>): EnvironmentVariables {
  const validated = plainToInstance(EnvironmentVariables, config, { enableImplicitConversion: true });
  const errors = validateSync(validated, { skipMissingProperties: false });
  if (errors.length > 0) throw new Error(`Invalid environment configuration: ${errors}`);
  return validated;
}
```

---

## RxJS for HTTP calls

```typescript
// Good — simple pass-through stays as an Observable, framework subscribes
getRealEstateTypes(): Observable<RealEstateType[]> {
  return this.http.get<RealEstateType[]>(`${this.baseUrl}/real-estate-types`).pipe(
    map((res) => res.data),
  );
}

// Good — lastValueFrom only when async/await ergonomics are genuinely needed
async deleteLead(id: string): Promise<void> {
  try {
    await lastValueFrom(this.http.delete(`${this.baseUrl}/leads/${id}`));
  } catch (error) {
    throw new HttpException(extractHttpData(error), extractHttpStatus(error));
  }
}

// Good — multi-request orchestration stays in operators, no mixed await
saveDraft(payload: SaveLeadDraftDto): Observable<{ id: string }> {
  return forkJoin([this.saveBuyer(payload), this.saveAddress(payload)]).pipe(
    switchMap(([buyer, address]) => this.finalizeDraft(buyer, address)),
    catchError((error) => {
      throw new HttpException(extractHttpData(error), extractHttpStatus(error));
    }),
  );
}

// Bad — awaiting an Observable directly instead of converting it first
async saveDraft(payload: SaveLeadDraftDto) {
  const buyer = await this.saveBuyer(payload); // saveBuyer() returns Observable<Buyer> — this resolves the Observable object, not its emitted value
}
```

Test doubles for `HttpService`:
```typescript
// Good
httpServiceMock.get.mockReturnValue(of({ data: mockTypes }));
httpServiceMock.get.mockReturnValue(throwError(() => ({ response: { status: 404 } })));
```

---

## Error mapping — extract and rethrow, no exception filters

```typescript
// Good
export function extractHttpStatus(error: unknown): number {
  return (error as UpstreamError)?.response?.status ?? 502;
}

export function extractHttpData(error: unknown): string | Record<string, unknown> {
  const data = (error as UpstreamError)?.response?.data;
  if (typeof data === 'string') return data;
  if (data !== null && typeof data === 'object') return data as Record<string, unknown>;
  return 'Bad Gateway';
}

// Usage at every upstream call site
throw new HttpException(extractHttpData(error), extractHttpStatus(error));

// Bad — swallowing the upstream status/body and always returning a generic 500
catch (error) {
  throw new InternalServerErrorException('Something went wrong');
}
```

---

## Logging — `Logger`, never `console.*`, never a token

```typescript
// Good
@Injectable()
export class LeadsService {
  private readonly logger = new Logger(LeadsService.name);

  fetchLead(id: string): void {
    this.logger.log(`Fetching lead ${id}`);
  }
}

// Bad — console.* in shipped code
console.info('fetching lead', id);

// Bad — logging a value that carries the auth token
console.log(url, params, authToken);
```

Latency/audit interceptor (either variant is fine):
```typescript
// Good — tap variant
return next.handle().pipe(tap({ next: logCompletion, error: logCompletion }));

// Good — finalize variant
return next.handle().pipe(finalize(logCompletion));
```

---

## Auth reality check

Don't invent a JWT guard. **Read what the project already does**: some BFFs only forward the `Authorization` header verbatim upstream; others authenticate at the edge. Internal S2S tokens, when present, use **that repository's** library/convention. Do not present `@UseGuards(AuthGuard('jwt'))` as a universal pattern. If a task needs inbound verification and the project doesn't have it yet, flag it as new infrastructure that needs a team decision.

---

## Anti-patterns checklist

| Anti-pattern | Correct alternative |
|---|---|
| Hand-typed module/controller boilerplate | `nest g <schematic> <name>` |
| Manual `new Service()` | Constructor injection |
| `@Inject(REQUEST)` + `Scope.DEFAULT` | `@Inject(REQUEST)` + `Scope.REQUEST` |
| Response DTO as a bare `interface` | Response DTO as a decorated `class` |
| `process.env['X']` inside a service | `ConfigService.get('X')` |
| `await` on an `Observable` directly | `lastValueFrom(obs)`, or keep it an `Observable` |
| Mixed `await` + operator chain in one method | Pure `Observable` pipeline (`switchMap`/`forkJoin`) or pure `async/await` — not both |
| `@Catch()` exception filter for upstream errors | `extractHttpStatus`/`extractHttpData` + rethrow `HttpException` |
| `console.log` / `console.info` / `console.error` | `Logger` per class |
| Logging a header, token, or `authToken` variable | Never — redact before logging, or don't log the call at all |
| `any` in test mocks | Typed mock objects (`jest.Mocked<T>` or an explicit interface) |
| Assuming a JWT guard exists to copy | Don't invent one — read the project's pattern (forward vs edge verify) |
