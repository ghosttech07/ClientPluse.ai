'use client';
import {useEffect,useRef} from 'react';

export default function SpaceCursorGlow(){
 const glow=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const el=glow.current;
  if(!el)return;
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  let frame=0,x=0,y=0;
  const hide=()=>{el.style.opacity='0';};
  const move=(event:PointerEvent)=>{
   if(motion.matches||event.pointerType!=='mouse'){hide();return;}
   x=event.clientX;y=event.clientY;
   if(frame)return;
   frame=requestAnimationFrame(()=>{frame=0;el.style.transform=`translate3d(${x}px,${y}px,0)`;el.style.opacity='.55';});
  };
  window.addEventListener('pointermove',move,{passive:true});
  document.addEventListener('pointerleave',hide);
  window.addEventListener('blur',hide);
  motion.addEventListener('change',hide);
  return()=>{cancelAnimationFrame(frame);window.removeEventListener('pointermove',move);document.removeEventListener('pointerleave',hide);window.removeEventListener('blur',hide);motion.removeEventListener('change',hide);};
 },[]);
 return <div ref={glow} className="space-cursor-glow" aria-hidden="true"><span/></div>;
}
