'use client';
import {useEffect,useRef} from 'react';

/** Keep keyboard navigation within an open modal and restore its trigger. */
export function useDialogFocus(open:boolean,onClose:()=>void){
 const ref=useRef<HTMLElement>(null),close=useRef(onClose);close.current=onClose;
 useEffect(()=>{
  if(!open)return;
  const previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
  const previous=document.activeElement as HTMLElement|null;
  const panel=ref.current;if(!panel){document.body.style.overflow=previousOverflow;return;}
  const controls=()=>Array.from(panel.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')).filter(e=>e.getClientRects().length>0);
  (panel.querySelector<HTMLElement>('[data-autofocus],[autofocus]')||controls()[0])?.focus();
  const key=(e:KeyboardEvent)=>{
   if(e.key==='Escape'){e.preventDefault();close.current();}
   if(e.key==='Tab'){
    const items=controls(),first=items[0],last=items[items.length-1];
    if(!first){e.preventDefault();return;}
    if(e.shiftKey&&(document.activeElement===first||!panel.contains(document.activeElement))){e.preventDefault();last.focus();}
    else if(!e.shiftKey&&(document.activeElement===last||!panel.contains(document.activeElement))){e.preventDefault();first.focus();}
   }
  };
  document.addEventListener('keydown',key);
  return()=>{document.body.style.overflow=previousOverflow;document.removeEventListener('keydown',key);previous?.focus();};
 },[open]);
 return ref;
}
