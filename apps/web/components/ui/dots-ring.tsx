'use client';
import {motion,useReducedMotion} from 'framer-motion';
export function DotsRing({size=48,className='',label}:{size?:number;className?:string;label?:string}){
 const reduced=useReducedMotion();
 return <span className={className.replace(/\bcp-spin\b/g,'')} role={label?'status':undefined} aria-label={label} aria-hidden={label?undefined:true} style={{position:'relative',display:'inline-flex',width:size,height:size,flexShrink:0,verticalAlign:'middle'}}><span className="relative w-12 h-12" style={{position:'absolute',top:0,left:0,transform:`scale(${size/48})`,transformOrigin:'top left'}}>{[0,1,2,3,4,5,6,7].map(i=><motion.span key={i} className="absolute top-0 left-1/2 w-2 h-2 rounded-full -ml-1 origin-[4px_24px]" style={{rotate:i*45,backgroundColor:'currentColor'}} animate={reduced?{scale:1,opacity:1}:{scale:[1,.5,1],opacity:[1,.3,1]}} transition={{duration:1.5,repeat:reduced?0:Infinity,delay:i*.15,ease:'easeInOut'}}/>)}</span></span>;
}
export default DotsRing;
