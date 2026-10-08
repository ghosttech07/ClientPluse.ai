import type { Metadata } from 'next';
import './tailwind.css';
import './globals.css';
import './light-theme.css';
import './landing-fluid.css';
import './workspace-polish.css';
export const metadata: Metadata = { title: 'EVIDENCE.AI — Every Format. One Intelligence.', description: 'Connect documents, images, audio, video, and data into traceable intelligence.' };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
