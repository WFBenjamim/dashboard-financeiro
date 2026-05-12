# Dashboard Financeiro

Aplicação Next.js do dashboard financeiro executivo, preparada para rodar localmente e para deploy no Vercel.

## Desenvolvimento

Instale as dependências e rode o servidor local:

```bash
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000).

O projeto roda em um compartilhamento de rede. Por isso, o script `dev` usa Webpack (`next dev --webpack`), evitando falhas do Turbopack com caminhos UNC. Em disco local, `npm run dev:turbo` também fica disponível.

## Dados

As planilhas mensais ficam em `data/` e continuam fora do Git por segurança. A planilha principal esperada pela esteira é `data/Orçamento.xlsx`.

Para atualizar o dashboard depois de trocar ou atualizar a planilha:

```bash
uv run --with pandas --with openpyxl python scripts/generate_static_data.py
```

Esse comando lê `data/Orçamento.xlsx`, processa as abas mapeadas no ETL e recria os snapshots JSON em `public/data`. O app Next.js consome esses JSONs localmente e no Vercel.

Se um backend for criado no futuro, configure `NEXT_PUBLIC_API_URL` para usar as rotas de API esperadas pela camada `lib/api.ts`.

## Build

```bash
npm run lint
npm run build
npm run start
```

## Deploy no Vercel

No Vercel, use as configurações padrão de projeto Next.js:

- Framework Preset: Next.js
- Build Command: `npm run build`
- Install Command: `npm install`
- Output Directory: `.next`
