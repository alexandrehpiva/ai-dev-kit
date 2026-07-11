# nest-patterns — padrões canônicos de NestJS

## Detecção de versão (sempre rode primeiro)

```bash
cat package.json | grep '"@nestjs/core"'
```

---

## Scaffolding — use a CLI, não escreva à mão

```bash
# Bom — gera um módulo de feature completo, depois adapte às convenções da casa
pnpm nest g resource leads

# Bom — gera um artefato por vez
pnpm nest g module leads
pnpm nest g controller leads
pnpm nest g service leads

# Ruim — digitar o boilerplate de módulo/controller à mão
# (perde os decorators, imports e esqueleto de spec corretos que a CLI já gera)
```

---

## Anatomia de módulo — feature-first

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
// Bom
@Module({
  controllers: [LeadsController],
  providers: [LeadsService],
})
export class LeadsModule {}
```

---

## Injeção de dependência — apenas por construtor

```typescript
// Bom
@Injectable()
export class LeadsService {
  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {}
}

// Ruim — instanciação manual, sem DI
export class LeadsService {
  private readonly http = new HttpService();
}
```

### Providers request-scoped — combine o scope corretamente

```typescript
// Bom — injeção de REQUEST combinada com scope REQUEST
@Injectable({ scope: Scope.REQUEST })
export class AuthService {
  constructor(@Inject(REQUEST) private readonly req: Request) {}
}

// Ruim — injeta REQUEST mas declara scope DEFAULT (singleton) — bug real, não atalho
@Injectable({ scope: Scope.DEFAULT })
export class AuthService {
  constructor(@Inject(REQUEST) req: Request) {}
}
```

---

## DTOs e validação

```typescript
// Bom — classe, decorada, validação aninhada
export class SaveLeadDraftDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @ValidateNested()
  @Type(() => AddressDto)
  address: AddressDto;
}

// Ruim — forma de resposta como interface pura (sem metadata do Swagger, não pode ser decorada)
export interface LeadDraftResponseDto {
  id: string;
  name: string;
}
```

Conecte o pipe global uma vez, em `main.ts`:
```typescript
app.useGlobalPipes(new ValidationPipe({ transform: true, whitelist: true }));
```

---

## Config de ambiente — `ConfigService`, nunca `process.env`

```typescript
// Bom
@Injectable()
export class LeadsService {
  private readonly baseUrl: string;

  constructor(config: ConfigService) {
    this.baseUrl = config.get<string>('MS_LEADS_URL') ?? '';
  }
}

// Ruim — leitura direta de process.env dentro de um service
export class LeadsService {
  private readonly baseUrl = process.env['MS_LEADS_URL'] ?? '';
}
```

Valide o formato uma vez, no bootstrap:
```typescript
export function validateEnv(config: Record<string, unknown>): EnvironmentVariables {
  const validated = plainToInstance(EnvironmentVariables, config, { enableImplicitConversion: true });
  const errors = validateSync(validated, { skipMissingProperties: false });
  if (errors.length > 0) throw new Error(`Invalid environment configuration: ${errors}`);
  return validated;
}
```

---

## RxJS para chamadas HTTP

```typescript
// Bom — pass-through simples permanece como Observable, o framework se inscreve
getRealEstateTypes(): Observable<RealEstateType[]> {
  return this.http.get<RealEstateType[]>(`${this.baseUrl}/real-estate-types`).pipe(
    map((res) => res.data),
  );
}

// Bom — lastValueFrom apenas quando a ergonomia de async/await é genuinamente necessária
async deleteLead(id: string): Promise<void> {
  try {
    await lastValueFrom(this.http.delete(`${this.baseUrl}/leads/${id}`));
  } catch (error) {
    throw new HttpException(extractHttpData(error), extractHttpStatus(error));
  }
}

// Bom — orquestração de múltiplas requisições permanece em operadores, sem await misturado
saveDraft(payload: SaveLeadDraftDto): Observable<{ id: string }> {
  return forkJoin([this.saveBuyer(payload), this.saveAddress(payload)]).pipe(
    switchMap(([buyer, address]) => this.finalizeDraft(buyer, address)),
    catchError((error) => {
      throw new HttpException(extractHttpData(error), extractHttpStatus(error));
    }),
  );
}

// Ruim — await direto em um Observable em vez de convertê-lo primeiro
async saveDraft(payload: SaveLeadDraftDto) {
  const buyer = await this.saveBuyer(payload); // saveBuyer() retorna Observable<Buyer> — isto resolve o objeto Observable, não o valor emitido
}
```

Dublês de teste para `HttpService`:
```typescript
// Bom
httpServiceMock.get.mockReturnValue(of({ data: mockTypes }));
httpServiceMock.get.mockReturnValue(throwError(() => ({ response: { status: 404 } })));
```

---

## Mapeamento de erro — extrair e relançar, sem exception filters

```typescript
// Bom
export function extractHttpStatus(error: unknown): number {
  return (error as UpstreamError)?.response?.status ?? 502;
}

export function extractHttpData(error: unknown): string | Record<string, unknown> {
  const data = (error as UpstreamError)?.response?.data;
  if (typeof data === 'string') return data;
  if (data !== null && typeof data === 'object') return data as Record<string, unknown>;
  return 'Bad Gateway';
}

// Uso em todo ponto de chamada ao upstream
throw new HttpException(extractHttpData(error), extractHttpStatus(error));

// Ruim — engole o status/corpo do upstream e sempre retorna um 500 genérico
catch (error) {
  throw new InternalServerErrorException('Something went wrong');
}
```

---

## Logging — `Logger`, nunca `console.*`, nunca um token

```typescript
// Bom
@Injectable()
export class LeadsService {
  private readonly logger = new Logger(LeadsService.name);

  fetchLead(id: string): void {
    this.logger.log(`Fetching lead ${id}`);
  }
}

// Ruim — console.* em código enviado
console.info('fetching lead', id);

// Ruim — logar um valor que carrega o token de auth
console.log(url, params, authToken);
```

Interceptor de latência/auditoria (as duas variantes são aceitas):
```typescript
// Bom — variante com tap
return next.handle().pipe(tap({ next: logCompletion, error: logCompletion }));

// Bom — variante com finalize
return next.handle().pipe(finalize(logCompletion));
```

---

## Checagem de realidade sobre auth

Não invente um JWT guard. **Leia o que o projeto já faz**: alguns BFFs apenas repassam o header `Authorization` verbatim para upstream; outros autenticam na borda. Tokens S2S internos, quando existirem, usam a lib/convenção **do repositório**. Não apresente `@UseGuards(AuthGuard('jwt'))` como padrão universal. Se a tarefa exigir verificação de entrada e o projeto ainda não tiver, sinalize como infraestrutura nova que precisa de decisão do time.

---

## Checklist de anti-padrões

| Anti-padrão | Alternativa correta |
|---|---|
| Boilerplate de módulo/controller digitado à mão | `nest g <schematic> <nome>` |
| `new Service()` manual | Injeção por construtor |
| `@Inject(REQUEST)` + `Scope.DEFAULT` | `@Inject(REQUEST)` + `Scope.REQUEST` |
| DTO de resposta como `interface` pura | DTO de resposta como `class` decorada |
| `process.env['X']` dentro de um service | `ConfigService.get('X')` |
| `await` direto em um `Observable` | `lastValueFrom(obs)`, ou mantenha como `Observable` |
| `await` misturado com cadeia de operadores no mesmo método | Pipeline `Observable` puro (`switchMap`/`forkJoin`) ou `async/await` puro — nunca os dois |
| Exception filter (`@Catch()`) para erros de upstream | `extractHttpStatus`/`extractHttpData` + relançar `HttpException` |
| `console.log` / `console.info` / `console.error` | `Logger` por classe |
| Logar um header, token, ou variável `authToken` | Nunca — redija antes de logar, ou não logue a chamada |
| `any` em mocks de teste | Objetos mock tipados (`jest.Mocked<T>` ou uma interface explícita) |
| Assumir que existe um JWT guard para copiar | Não invente — leia o padrão do projeto (forward vs verify na borda) |
