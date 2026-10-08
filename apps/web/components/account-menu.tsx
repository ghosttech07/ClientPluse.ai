'use client';
import {DotsRing} from './ui/dots-ring';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {BookOpen,ChevronDown,LogOut,Settings,UserRound} from 'lucide-react';
import {supabase} from '@/lib/api';
import {pulse,Settings as CompanySettings} from '@/lib/pulse';

export function AccountMenu({company}:{company?:string}){
 const [account,setAccount]=useState<{name:string;email:string}|null>(null),[workspace,setWorkspace]=useState(company||''),[open,setOpen]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const root=useRef<HTMLDivElement>(null);const router=useRouter();
 useEffect(()=>{
  const update=(user:{email?:string;user_metadata:Record<string,unknown>}|null)=>setAccount(user?{name:String(user.user_metadata.full_name||user.user_metadata.name||user.email?.split('@')[0]||'Your account'),email:user.email||''}:null);
  let active=true;supabase?.auth.getSession().then(({data})=>{if(active)update(data.session?.user||null);});
  const subscription=supabase?.auth.onAuthStateChange((_,session)=>{if(active)update(session?.user||null);});
  return()=>{active=false;subscription?.data.subscription.unsubscribe();};
 },[]);
 useEffect(()=>{if(company){setWorkspace(company);return;}if(!account)return;let active=true;void pulse<CompanySettings>('/settings').then(value=>{if(active)setWorkspace(value.onboarding_required?'Company setup pending':value.name);}).catch(()=>{});return()=>{active=false;};},[company,account]);
 useEffect(()=>{if(!open)return;const outside=(event:PointerEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false);};const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'){setOpen(false);root.current?.querySelector('button')?.focus();}};document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};},[open]);
 if(!account)return null;
 async function logout(){setBusy(true);setError('');const result=await supabase?.auth.signOut();if(result?.error){setError(result.error.message);setBusy(false);return;}setOpen(false);router.replace('/login');}
 return <div className="cp-user-menu" ref={root}><button className="cp-user-trigger" aria-label="Your account" aria-expanded={open} onClick={()=>setOpen(!open)}><span className="cp-avatar"><UserRound size={18}/></span><span className="cp-user-name">{account.name}</span><ChevronDown size={14}/></button>{open&&<section className="cp-user-popover" aria-label="Account details"><strong>{account.name}</strong><span>{account.email}</span><small>{workspace}</small><Link href="/dashboard/settings" onClick={()=>setOpen(false)}><Settings size={16}/>Company settings</Link><Link href="/dashboard/manual" onClick={()=>setOpen(false)}><BookOpen size={16}/>User manual</Link>{error&&<p role="alert">{error}</p>}<button disabled={busy} onClick={()=>void logout()}>{busy?<DotsRing size={16}/>:<LogOut size={16}/>} {busy?'Signing out…':'Sign out'}</button></section>}</div>;
}
