# Landing background: React Bits LiquidEther

Installed the **JS-CSS** variant directly from the user-specified registry:
https://reactbits.dev/r/LiquidEther-JS-CSS.json

- Exact, unmodified registry files: `apps/web/components/LiquidEther/LiquidEther.jsx` and `LiquidEther.css`.
- Registry copy for provenance: `data/reactbits/LiquidEther-JS-CSS.json`.
- Listed dependency: `three@^0.180.0`, already installed and verified.
- Integration: `apps/web/components/liquid-landing-background.tsx`, imported only by the landing page.
- All user-provided configuration values are retained, including colors, resolution 0.5, 32 pressure iterations, cursor size 100, mouse force 20 and idle demo/resume settings.

The integration uses a client-only dynamic import for Next.js. The fixed full-viewport background fills the landing page behind the existing content instead of adding a separate 600-pixel demo block. Pointer events continue to reach links; LiquidEther listens for mouse/touch movements on the window. The canvas does not capture mobile scrolling. Reduced-motion preference uses the static dark background, and a WebGL error boundary keeps the page usable on unsupported devices. No effect is mounted on login, dashboard or workspace routes.

Registry installation was done directly, preserving the exact source and plain CSS without adding an unrelated Tailwind/shadcn UI configuration.

Documentation: https://reactbits.dev/backgrounds/liquid-ether
