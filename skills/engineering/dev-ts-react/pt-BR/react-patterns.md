# react-patterns — padrões canônicos de React SPA (Vite)

## Detecção de versão e stack (sempre rode primeiro)

```bash
cat package.json | grep -E '"react"|"vite"|"react-router"|"@tanstack/react-query"'
```

---

## Anatomia de feature — feature-first

```
src/features/monthly-entries/
  components/
    MonthlyEntryForm.tsx
    MonthlyEntryForm.test.tsx
    MonthlyEntryList.tsx
  hooks/
    useMonthlyEntries.ts
  api/
    monthlyEntriesClient.ts   # funções tipadas de chamada HTTP, sem lógica de UI
  types.ts
```

```
src/components/ui/          # componentes de apresentação compartilhados (Button, Input, Modal)
src/hooks/                  # hooks compartilhados entre features (useAuth, useDebounce)
src/lib/                    # cliente HTTP base, config, utilitários puros
```

---

## Componente — função + props tipadas

```tsx
// Bom
interface MonthlyEntryFormProps {
  initialValue?: MonthlyEntry;
  onSubmit: (entry: MonthlyEntryInput) => void;
}

export function MonthlyEntryForm({ initialValue, onSubmit }: MonthlyEntryFormProps) {
  // ...
}

// Ruim — props soltas sem interface, any implícito
export function MonthlyEntryForm(props: any) { /* ... */ }
```

---

## Data fetching — camada dedicada, nunca useEffect manual

```tsx
// api/monthlyEntriesClient.ts
export async function fetchMonthlyEntries(tenantId: string): Promise<MonthlyEntry[]> {
  const res = await apiClient.get(`/tenants/${tenantId}/monthly-entries`);
  return res.data;
}

// hooks/useMonthlyEntries.ts
export function useMonthlyEntries(tenantId: string) {
  return useQuery({
    queryKey: ["monthly-entries", tenantId],
    queryFn: () => fetchMonthlyEntries(tenantId),
  });
}
```

```tsx
// Ruim — busca manual com useEffect/useState, perde cache/retry/estado de loading de graça
function MonthlyEntryList() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch("/api/monthly-entries").then((r) => r.json()).then(setData);
  }, []);
  // ...
}
```

`useEffect` continua legítimo para sincronizar com algo **fora do React**: título do documento, subscription de WebSocket, listener de evento do DOM, timer.

---

## Estados de UI — loading/erro/sucesso explícitos

```tsx
// Bom
function MonthlyEntryList({ tenantId }: { tenantId: string }) {
  const { data, isLoading, isError, error } = useMonthlyEntries(tenantId);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState message={error.message} />;
  if (data.length === 0) return <EmptyState />;

  return <ul>{data.map((entry) => <MonthlyEntryRow key={entry.id} entry={entry} />)}</ul>;
}

// Ruim — sem tratar loading/erro, assume que data sempre existe
function MonthlyEntryList({ tenantId }: { tenantId: string }) {
  const { data } = useMonthlyEntries(tenantId);
  return <ul>{data.map((entry) => <MonthlyEntryRow key={entry.id} entry={entry} />)}</ul>;
}
```

Controles que disparam ação assíncrona (botão de salvar, toggle) ficam `disabled` durante a chamada e refletem o estado real após a resposta — nunca um estado otimista que a UI não confirma.

---

## Formulário — schema único compartilhado

```tsx
const monthlyEntrySchema = z.object({
  description: z.string().min(1, "Descrição obrigatória"),
  amount: z.number().positive("Valor deve ser maior que zero"),
  dueDate: z.string().date(),
});

type MonthlyEntryInput = z.infer<typeof monthlyEntrySchema>;

function MonthlyEntryForm({ onSubmit }: MonthlyEntryFormProps) {
  const form = useForm<MonthlyEntryInput>({ resolver: zodResolver(monthlyEntrySchema) });
  // form.formState.errors já reflete as mensagens do schema, sem duplicar validação no JSX
}
```

O mesmo `monthlyEntrySchema` (ou um `.pick()`/`.omit()` dele) valida o payload antes de enviar à API — não escreva uma segunda validação manual no client da API.

---

## Teste de componente — comportamento, não implementação

```tsx
// Bom
test("mostra erro quando valor é zero", async () => {
  render(<MonthlyEntryForm onSubmit={vi.fn()} />);
  await userEvent.type(screen.getByLabelText("Valor"), "0");
  await userEvent.click(screen.getByRole("button", { name: "Salvar" }));
  expect(await screen.findByText("Valor deve ser maior que zero")).toBeVisible();
});

// Ruim — testa estado interno em vez do que o usuário vê
test("seta amount para 0", () => {
  const { result } = renderHook(() => useState(0));
  expect(result.current[0]).toBe(0);
});
```

Mocke a rede com MSW (intercepta a request real do client tipado) em vez de mockar o componente ou o hook — assim o teste também cobre a integração `hook → client → componente`.

---

## Tabela de anti-padrões

| Anti-padrão | Por quê é problema | Correção |
|---|---|---|
| `useEffect` + `fetch` manual para dados de servidor | Perde cache, retry, dedupe, estado de loading — reimplementa o que a lib de data-fetching já resolve | `useQuery`/`useMutation` |
| Prop drilling de 4+ níveis | Componente intermediário só repassa prop sem usá-la — acopla toda a árvore | Context/store só quando o compartilhamento é genuinamente distante |
| `any` em props ou retorno de API | Perde checagem de tipo exatamente onde mais importa (borda de dado externo) | `interface`/`type` explícito, `zod` para validar o shape em runtime na borda |
| Validação duplicada (schema + `if` manual no submit) | Duas fontes de verdade divergem com o tempo | Um schema único, reusado no form e no client da API |
| `div onClick` no lugar de `button` | Quebra navegação por teclado e leitor de tela | Elemento semântico correto + label associado |
| Componente que assume sucesso sem checar `isError`/`isLoading` | Tela quebra ou mostra dado stale quando a API falha | Tratar os três estados explicitamente |
