'use client';
import dynamic from 'next/dynamic';
import {Component,useEffect,useState} from 'react';
const LiquidEther=dynamic(()=>import('./LiquidEther/LiquidEther'),{ssr:false});
const colors=['#5227FF','#FF9FFC','#B497CF'];
class WebGLFallback extends Component<{children:React.ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true};}render(){return this.state.failed?null:this.props.children;}}
export default function LiquidLandingBackground(){
 const [animate,setAnimate]=useState(false),[resolution,setResolution]=useState(0.3);
 useEffect(()=>{setResolution(matchMedia('(max-width: 768px)').matches?0.22:0.3);const motion=matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setAnimate(!motion.matches);update();motion.addEventListener('change',update);return()=>motion.removeEventListener('change',update);},[]);
 return <div className="landing-liquid-background" aria-hidden="true">{animate&&<WebGLFallback><LiquidEther colors={colors} mouseForce={20} cursorSize={100} isViscous={false} viscous={30} iterationsViscous={32} iterationsPoisson={16} resolution={resolution} isBounce={false} autoDemo={true} autoSpeed={0.5} autoIntensity={2.2} takeoverDuration={0.25} autoResumeDelay={800} autoRampDuration={1.2}/></WebGLFallback>}</div>;
}
