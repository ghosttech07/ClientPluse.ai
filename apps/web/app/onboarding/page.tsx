'use client';
import {DotsRing} from '@/components/ui/dots-ring';
import {WorkspaceGlow} from '@/components/workspace-glow';
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowRight,Building2} from 'lucide-react';
import {PulseBrand} from '@/components/pulse-shell';
import {AccountMenu} from '@/components/account-menu';
import {supabase} from '@/lib/api';
import {pulse,Settings} from '@/lib/pulse';

export default function CompanySetup(){
 const router=useRouter();const [name,setName]=useState(''),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let active=true;(async()=>{
  try{
   const session=await supabase?.auth.getSession();if(!session?.data.session){router.replace('/login');return;}
   const settings=await pulse<Settings>('/settings');if(!active)return;
   if(!settings.onboarding_required){router.replace('/dashboard');return;}
   setName(settings.name==='My organization'?'':settings.name);setLoading(false);
  }catch(e){if(active){setError((e as Error).message);setLoading(false);}}
 })();return()=>{active=false;};},[router]);
 async function submit(event:React.FormEvent){event.preventDefault();if(name.trim().length<2){setError('Enter your company name.');return;}setBusy(true);setError('');try{await pulse('/onboarding',{method:'POST',body:JSON.stringify({name:name.trim()})});router.replace('/dashboard');}catch(e){setError((e as Error).message);setBusy(false);}}
 return <WorkspaceGlow><main className="pulse cp-auth"><div className="cp-auth-wrap"><div className="cp-auth-brandbar"><PulseBrand href="/onboarding"/><AccountMenu/></div><section className="cp-auth-card"><span className="cp-eyebrow">LET’S SET UP YOUR WORKSPACE</span><h1 style={{marginTop:12}}>What’s your company name?</h1><p>Give your workspace a name before connecting customers and their conversations.</p>{error&&<div className="cp-notice cp-error" role="alert">{error}</div>}{loading?<p><DotsRing className="cp-spin" size={18}/> Checking your workspace…</p>:<form onSubmit={submit}><label>Company name<input autoFocus autoComplete="organization" value={name} onChange={e=>setName(e.target.value)} placeholder="Enter your company name" minLength={2} maxLength={160} required disabled={busy}/></label><button className="cp-button" disabled={busy||name.trim().length<2}>{busy?<DotsRing className="cp-spin" size={17}/>:<Building2 size={17}/>}Continue to workspace <ArrowRight size={17}/></button></form>}</section></div></main></WorkspaceGlow>;
}
