import PulseDashboard from '@/components/pulse-dashboard';
import {notFound} from 'next/navigation';
export default async function Page({params}:{params:Promise<{section:string}>}){const {section}=await params;if(!['customers','intelligence','complaints','uploads','alerts','reports','settings'].includes(section))notFound();return <PulseDashboard section={section}/>;}
