# Landing UI components

The frontend already uses TypeScript and the `@/*` alias, rooted at `apps/web`. Shared UI components live in `apps/web/components/ui`; this conventional folder keeps registry imports consistent with shadcn tooling. App components remain in `apps/web/components`. Global styles are in `apps/web/app`, and React Bits component CSS stays beside each component.

Tailwind is configured through `apps/web/postcss.config.mjs` and `apps/web/app/tailwind.css`. Utilities are enabled without replacing the existing application's CSS reset. `apps/web/components.json` supplies shadcn aliases, and `apps/web/lib/utils.ts` supplies `cn`.

The provided navigation component lives in `components/ui/nav-header.tsx`. It retains the supplied moving pill effect while using actual landing section links, typed position state, keyboard focus support, reduced-motion support and the existing mobile menu. No context provider or image assets are required. Framer Motion was already installed. The illustrative standalone demo page was not added to the product.

To add a shadcn component, run from `apps/web`:

```sh
npx shadcn@latest add button
```

For a new project without this setup, initialize with `npx shadcn@latest init`. Tailwind dependencies are `tailwindcss`, `@tailwindcss/postcss` and `postcss`; TypeScript dependencies are `typescript`, `@types/react` and `@types/node`.

Setup references: [Tailwind Next.js installation](https://tailwindcss.com/docs/installation/framework-guides/nextjs), [shadcn manual installation](https://ui.shadcn.com/docs/installation/manual).

React Bits SpecularButton uses the supplied JS-CSS source plus `ogl`. Landing actions and the mobile menu use it. It caps device pixel ratio and rendering frequency, pauses offscreen, and keeps usable plain buttons for reduced-motion or unavailable WebGL.
