# ANTI-PATTERNS — O que não fazer

## Bom / Ruim

### Paths locais

- **Ruim:** default `~/Projects/acme/service-a` no código versionado.  
- **Bom:** obrigar `config.yaml` / env; falhar com “copie o example”.

### Orquestração

- **Ruim:** um único `docker-compose.yml` “da empresa” que reimplementa todos os serviços.  
- **Bom:** chamar o Compose/Makefile que já vive em cada repo.

- **Ruim:** `service1 & service2 & wait` num script bash sem health nem `down`.  
- **Bom:** CLI com ondas, health, state e `down`.

- **Ruim:** todos os logs no mesmo terminal.  
- **Bom:** uma janela/painel por serviço (salvo escolha explícita do usuário).

### Portas e env

- **Ruim:** reescrever `.env` dos outros repos a cada `up`.  
- **Bom:** injetar env/templates só no processo lançado.

- **Ruim:** `pnpm start -- --port 4200` quando o script já é `ng serve` (vaza `--` e quebra schema).  
- **Bom:** `pnpm exec ng serve --port 4200` (ou equivalente limpo).

### Runtime

- **Ruim:** forçar `uvicorn` em app Flask/WSGI.  
- **Bom:** `gunicorn --reload` (ou o server WSGI correto) no override do catálogo.

### Escopo

- **Ruim:** MVP = Central + Portal + 15 serviços “já que estamos”.  
- **Bom:** uma jornada validável; próximas stacks no roadmap.

### Pré-requisitos

- **Ruim:** `brew install` silencioso de terminal emulator.  
- **Bom:** detectar ausência e instruir o usuário.

### “Pronto”

- **Ruim:** “deve funcionar” sem rodar `status` / check da jornada.  
- **Bom:** evidência fresca conforme `VALIDATION.md`.
