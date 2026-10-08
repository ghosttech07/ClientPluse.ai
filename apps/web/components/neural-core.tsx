'use client';
import { Canvas, useFrame } from '@react-three/fiber';
import { useMemo, useRef, useState, useEffect, Component } from 'react';
import * as THREE from 'three';
function Network({ reduced }: { reduced: boolean }) {
  const group=useRef<THREE.Group>(null);
  const { points, lines }=useMemo(()=>{
    const p:number[]=[]; const l:number[]=[]; const count=410;
    for(let i=0;i<count;i++){const y=1-2*i/(count-1),r=Math.sqrt(1-y*y),t=i*2.399963; p.push(Math.cos(t)*r*2.15,y*2.15,Math.sin(t)*r*2.15);}
    for(let i=0;i<count;i++){for(let j=i+1;j<count;j++){const d=Math.hypot(p[i*3]-p[j*3],p[i*3+1]-p[j*3+1],p[i*3+2]-p[j*3+2]);if(d<.48)l.push(...p.slice(i*3,i*3+3),...p.slice(j*3,j*3+3));}}
    return {points:new Float32Array(p),lines:new Float32Array(l)};
  },[]);
  useFrame((_,delta)=>{if(group.current&&!reduced){group.current.rotation.y+=delta*.3;}});
  return <group ref={group} rotation={[.1,.4,.1]}><points><bufferGeometry><bufferAttribute attach="attributes-position" args={[points,3]}/></bufferGeometry><pointsMaterial color="#e0b9ff" size={.035} transparent opacity={.9} sizeAttenuation/></points><lineSegments><bufferGeometry><bufferAttribute attach="attributes-position" args={[lines,3]}/></bufferGeometry><lineBasicMaterial color="#ad61cf" transparent opacity={.3}/></lineSegments><mesh><sphereGeometry args={[1.2,32,32]}/><meshBasicMaterial color="#8f5dba" transparent opacity={.12} wireframe/></mesh><mesh rotation={[Math.PI/2.8,.5,.2]}><torusGeometry args={[2.48,.008,8,120]}/><meshBasicMaterial color="#a475cc" transparent opacity={.45}/></mesh><mesh rotation={[Math.PI/1.6,.1,-.5]}><torusGeometry args={[2.7,.005,8,120]}/><meshBasicMaterial color="#945ab7" transparent opacity={.35}/></mesh></group>;
}
class SafeCanvas extends Component<{children:React.ReactNode},{failed:boolean}> { state={failed:false}; static getDerivedStateFromError(){return {failed:true};} render(){return this.state.failed?<div className="sphere-fallback"/>:this.props.children;} }
export default function NeuralCore(){
  const [ready,setReady]=useState(false),[reduced,setReduced]=useState(false),[visible,setVisible]=useState(true);
  const container=useRef<HTMLDivElement>(null);
  useEffect(()=>{const observer=new IntersectionObserver(([entry])=>setVisible(entry.isIntersecting));if(container.current)observer.observe(container.current);return()=>observer.disconnect();},[]);
  useEffect(()=>{setReady(true);setReduced(matchMedia('(prefers-reduced-motion: reduce)').matches);},[]);
  return <div ref={container} className="neural-canvas" style={{pointerEvents:'none'}} aria-label="Connected multimodal intelligence sphere">{ready?<SafeCanvas><Canvas frameloop={visible?(reduced?"demand":"always"):"never"} dpr={1} camera={{position:[0,0,6.7],fov:48}} gl={{antialias:true,alpha:true}}><Network reduced={reduced}/></Canvas></SafeCanvas>:<div className="sphere-fallback"/>}</div>;
}


