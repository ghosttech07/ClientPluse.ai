# Landing background: React Bits LiquidEther

Installed the **JS-CSS** variant directly from the user-specified registry:
https://reactbits.dev/r/LiquidEther-JS-CSS.json

- Registry component with local scroll-performance adjustments: `apps/web/components/LiquidEther/LiquidEther.jsx` and `LiquidEther.css`.
- Registry copy for provenance: `data/reactbits/LiquidEther-JS-CSS.json`.
- Listed dependency: `three@^0.180.0`, already installed and verified.
- Integration: `apps/web/components/liquid-landing-background.tsx`, imported only by the landing page.
- Colors, cursor size 100 and mouse force 20 are retained. Performance tuning uses resolution 0.3 on desktop and 0.22 on mobile, with 16 pressure iterations.

The integration uses a client-only dynamic import for Next.js. The fixed full-viewport background fills the landing page behind the existing content instead of adding a separate 600-pixel demo block. Pointer events continue to reach links; LiquidEther listens for mouse/touch movements on the window. The canvas does not capture mobile scrolling. Reduced-motion preference uses the static dark background, and a WebGL error boundary keeps the page usable on unsupported devices. No effect is mounted on login, dashboard or workspace routes.

Registry installation was done directly using plain CSS. The fluid simulation runs continuously on requestAnimationFrame, including during scrolling. The fullscreen output uses pixel ratio 1 without multisample antialiasing; the reduced simulation resolution and pressure iterations lower GPU work rather than freezing the animation. The globe renders at device pixel ratio 1 and pauses offscreen. The header avoids a live backdrop blur.

Documentation: https://reactbits.dev/backgrounds/liquid-ether


Idle motion resumes after 800 ms without pointer movement, even if the pointer stays inside the page, with a 1.2-second ramp. Scrolling does not stop the render loop.
