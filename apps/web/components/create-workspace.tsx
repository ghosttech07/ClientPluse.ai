'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, ArrowRight, Factory, GraduationCap, Shield, Package } from 'lucide-react';
import { api, industries, Workspace } from '@/lib/api';
const Icons=[Factory,GraduationCap,Shield,Package];
export function CreateWorkspace({onClose,initial='Manufacturing'}:{onClose:()=>void;initial?:string}){
 const [industry,setIndustry]=useState(initial),[name,setName]=useState(''),[description,setDescription]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');const router=useRouter();
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);try{const w=await api<Workspace>('/workspaces',{method:'POST',body:JSON.stringify({name,description,industry})});router.push('/workspace/'+w.id);}catch(e){setError((e as Error).message);setBusy(false);}}
 return <div className="modal-backdrop"><section role="dialog" aria-modal="true" aria-labelledby="create-title" className="modal"><div className="modal-header"><div><span className="overline">A NEW PERSPECTIVE</span><h2 id="create-title">Create a workspace</h2></div><button onClick={onClose} className="icon-button" aria-label="Close dialog"><X/></button></div><p>Choose your industry. Connect your evidence.</p><form onSubmit={submit}><label>Industry</label><div className="industry-options">{industries.map((v,i)=>{const Icon=Icons[i];return <button type="button" key={v.name} className={industry===v.name?'selected':''} onClick={()=>setIndustry(v.name)}><Icon size={19}/>{v.name}</button>;})}</div><label>Workspace name<input autoFocus required minLength={2} maxLength={160} value={name} onChange={e=>setName(e.target.value)} placeholder="e.g. Machine A — October investigation"/></label><label>Description<textarea value={description} onChange={e=>setDescription(e.target.value)} maxLength={3000} placeholder="What are you investigating or learning?" rows={3}/></label>{error&&<div className="error-banner">{error}</div>}<button className="button primary full" disabled={busy}>{busy?'Creating workspace…':'Create workspace'}<ArrowRight size={16}/></button></form></section></div>;
}
