"use client";
import {useEffect,useState} from 'react';
import {useParams} from 'next/navigation';
import ReactMarkdown from 'react-markdown';
export default function SharedChat(){const {token}=useParams<{token:string}>();const [data,setData]=useState<{messages:{role:string;content:string}[]}|null>(null);const [error,setError]=useState('');useEffect(()=>{fetch('/api/shared-chat/'+token).then(async r=>{if(!r.ok)throw Error('Shared chat unavailable.');setData(await r.json());}).catch(e=>setError(e.message));},[token]);return <main className="pulse" style={{padding:32,maxWidth:1000,margin:'auto'}}><h1>ClientPulse AI · Shared chat</h1><p>Read-only snapshot. Private files are not included.</p>{error?<p role="alert">{error}</p>:data?data.messages.map((message,i)=><article className={'cp-chat-message cp-'+message.role} key={i}><strong>{message.role==='user'?'You':'ClientPulse AI'}</strong><ReactMarkdown>{message.content}</ReactMarkdown></article>):<p>Loading…</p>}</main>;}
