'use client';
import {useEffect,useRef,useState,type ReactNode} from 'react';

const cards='.cp-panel,.cp-stat,.cp-auth-card,.cp-form-modal';
export function WorkspaceGlow({children}:{children:ReactNode}){
 const root=useRef<HTMLDivElement>(null);const [theme,setTheme]=useState('light');
 useEffect(()=>{const sync=()=>setTheme(localStorage.getItem('cp-theme')==='dark'?'dark':'light');sync();window.addEventListener('cp-theme-change',sync);window.addEventListener('storage',sync);return()=>{window.removeEventListener('cp-theme-change',sync);window.removeEventListener('storage',sync);};},[]);
 useEffect(()=>{
  const container=root.current;if(!container)return;
  let frame=0,active:HTMLElement|null=null,x=0,y=0;
  const clear=()=>{active?.removeAttribute('data-glow');active=null;};
  const move=(event:PointerEvent)=>{
   if(event.pointerType!=='mouse')return;
   const card=(event.target as Element).closest<HTMLElement>(cards);
   if(card!==active){clear();active=card;}
   if(!card||!container.contains(card))return;
   const bounds=card.getBoundingClientRect();x=event.clientX-bounds.left;y=event.clientY-bounds.top;
   card.dataset.glow='true';
   if(frame)return;
   frame=requestAnimationFrame(()=>{frame=0;active?.style.setProperty('--glow-x',`${x}px`);active?.style.setProperty('--glow-y',`${y}px`);});
  };
  container.addEventListener('pointermove',move,{passive:true});container.addEventListener('pointerleave',clear);
  return()=>{cancelAnimationFrame(frame);container.removeEventListener('pointermove',move);container.removeEventListener('pointerleave',clear);clear();};
 },[]);
 return <div ref={root} className="cp-glow-workspace" data-theme={theme}>{children}</div>;
}
