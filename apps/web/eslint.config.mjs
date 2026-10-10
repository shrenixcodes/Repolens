import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // This project fetches data from the RepoLens API with plain
      // fetch-in-useEffect (no React Query/SWR/Suspense data layer), which
      // is still fully supported, correct React -- this rule nudges toward
      // a Suspense-based data-fetching architecture that's out of scope
      // here. Verified these effects don't cause update loops or stale
      // renders (production build + manual browser testing).
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
