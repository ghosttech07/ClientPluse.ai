import type { Metadata } from 'next';
import './tailwind.css';
import './globals.css';
import './clientpulse.css';
import './workspace-design.css';
export const metadata: Metadata = { title: 'ClientPulse AI — Customer signals. Connected.', description: 'Detect customer dissatisfaction before it becomes customer churn. Connect communications and act with source-backed context.' };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
