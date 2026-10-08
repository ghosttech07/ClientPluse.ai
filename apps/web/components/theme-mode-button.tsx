'use client';
import {useEffect,useState} from 'react';
import {Moon,Sun} from 'lucide-react';
export function ThemeModeButton(){
 const [dark,setDark]=useState(false);
 useEffect(()=>{const sync=()=>setDark(localStorage.getItem('cp-theme')==='dark');sync();window.addEventListener('cp-theme-change',sync);window.addEventListener('storage',sync);return()=>{window.removeEventListener('cp-theme-change',sync);window.removeEventListener('storage',sync);};},[]);
 function toggle(){localStorage.setItem('cp-theme',dark?'light':'dark');window.dispatchEvent(new Event('cp-theme-change'));}
 return <button type="button" className="cp-theme-mode" onClick={toggle} aria-label={dark?'Switch to day mode':'Switch to night mode'} aria-pressed={dark}>{dark?<Moon size={18}/>:<Sun size={18}/>}<span>{dark?'Night mode':'Day mode'}</span></button>;
}
