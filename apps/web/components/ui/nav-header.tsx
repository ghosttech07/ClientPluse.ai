"use client";
import {useRef,useState} from 'react';
import {motion,useReducedMotion} from 'framer-motion';
type Position={left:number;width:number;opacity:number};
const links=[{label:'Platform',href:'#platform'},{label:'How it works',href:'#workflow'},{label:'Evidence & trust',href:'#trust'}];
export default function NavHeader({open=false,onNavigate}:{open?:boolean;onNavigate?:()=>void}){
  const [position,setPosition]=useState<Position>({left:0,width:0,opacity:0});
  const reduced=useReducedMotion();
  return <nav aria-label="Main navigation" className={open?'nav-links open':'nav-links'}>
    <ul className="nav-pill relative mx-auto flex w-fit rounded-full border p-1" onMouseLeave={()=>setPosition(previous=>({...previous,opacity:0}))} onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget))setPosition(previous=>({...previous,opacity:0}));}}>
      {links.map(link=><Tab key={link.href} {...link} setPosition={setPosition} onNavigate={onNavigate}/>)}
      <motion.li aria-hidden="true" animate={position} transition={reduced?{duration:0}:{type:'spring',stiffness:420,damping:35}} className="nav-pill-cursor absolute z-0 rounded-full"/>
    </ul>
  </nav>;
}
function Tab({label,href,setPosition,onNavigate}:{label:string;href:string;setPosition:(value:Position)=>void;onNavigate?:()=>void}){
  const ref=useRef<HTMLLIElement>(null);
  function highlight(){if(ref.current)setPosition({width:ref.current.getBoundingClientRect().width,left:ref.current.offsetLeft,opacity:1});}
  return <li ref={ref} onMouseEnter={highlight} className="relative z-10 block cursor-pointer text-white"><a href={href} onFocus={highlight} onClick={onNavigate} className="block whitespace-nowrap rounded-full px-3 py-3 text-xs md:px-5">{label}</a></li>;
}

