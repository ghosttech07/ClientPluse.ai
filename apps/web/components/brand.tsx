import { ScanLine } from 'lucide-react';
import Link from 'next/link';
export function Brand({ small = false }: { small?: boolean }) { return <Link className={`brand ${small ? 'small' : ''}`} href="/" aria-label="Evidence AI home"><span className="brand-mark"><ScanLine size={22}/></span><span>EVIDENCE<span className="brand-ai">.AI</span></span></Link>; }
