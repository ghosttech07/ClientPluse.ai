'use client';
import {useEffect,useRef} from 'react';
import dynamic from 'next/dynamic';
import {X} from 'lucide-react';
const AccountSignIn=dynamic(()=>import('./account-sign-in'),{loading:()=> <p className="sign-in-loading">Loading sign-in…</p>});
export default function SignInModal({onClose}:{onClose:()=>void}){
  const dialog=useRef<HTMLDialogElement>(null);
  useEffect(()=>{
    dialog.current?.showModal();
    const previous=document.body.style.overflow;
    document.body.style.overflow='hidden';
    return()=>{document.body.style.overflow=previous;};
  },[]);
  return <dialog ref={dialog} className="sign-in-modal" aria-label="Sign in to Evidence.ai" onCancel={onClose} onClick={event=>{if(event.target===event.currentTarget)onClose();}}>
    <button className="sign-in-close icon-button" aria-label="Close sign-in" onClick={onClose}><X size={20}/></button>
    <AccountSignIn compact/>
  </dialog>;
}
