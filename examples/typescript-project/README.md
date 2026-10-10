# Example: typescript-project

A tiny cart/checkout UI slice demonstrating TS classes/interfaces/types,
cross-file imports, and TSX components with real import relationships
(`CartSummary.tsx` imports `Cart`, `formatCurrency`, and `Button`).

```bash
cd examples/typescript-project
repolens init
repolens index
repolens search "cart total"
repolens impact src/cart.ts
repolens impact src/format.ts::formatCurrency
repolens graph   # (via the web UI -- see the root README)
```

`repolens impact src/cart.ts` should show `src/components/CartSummary.tsx`
as a dependent.
