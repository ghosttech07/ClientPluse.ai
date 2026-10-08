'use client';
import {useEffect,useRef,type ReactNode} from 'react';

const cards='.cp-panel,.cp-stat,.cp-auth-card,.cp-form-modal';
export function WorkspaceGlow({children}:{children:ReactNode}){
 const root=useRef<HTMLDivElement>(null);
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
 return <div ref={root} className="cp-glow-workspace">{children}</div>;
}
