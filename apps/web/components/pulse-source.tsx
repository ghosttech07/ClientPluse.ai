'use client';
import {useEffect,useState} from 'react';
import {X,ExternalLink,LoaderCircle} from 'lucide-react';
import {fileBlob} from '@/lib/api';
import {Source} from '@/lib/pulse';
import {useDialogFocus} from './use-dialog-focus';
export function PulseSource({source,onClose}:{source:Source;onClose:()=>void}){
 const [url,setUrl]=useState(''),[error,setError]=useState('');
 const dialogRef=useDialogFocus(true,onClose);
 useEffect(()=>{let active=true,objectURL='';fileBlob('/v1/uploads/'+source.file_id+'/content').then(blob=>{objectURL=URL.createObjectURL(blob);if(active)setUrl(objectURL);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;if(objectURL)URL.revokeObjectURL(objectURL);};},[source.file_id]);

 return <div className="cp-modal-backdrop" onClick={onClose}><section ref={dialogRef} role="dialog" aria-modal="true" aria-label="Source evidence" className="cp-source-modal" onClick={e=>e.stopPropagation()}><header><div><span className="cp-eyebrow">ORIGINAL EVIDENCE</span><h2>{source.file_name}</h2></div><button autoFocus className="cp-icon" aria-label="Close evidence" onClick={onClose}><X/></button></header><div className="cp-source-meta">{source.event_time?new Date(source.event_time).toLocaleString():'Communication date unknown'}{source.page&&' · Page '+source.page}{source.timestamp!==undefined&&source.timestamp!==null&&' · '+source.timestamp+' seconds'}</div><blockquote>{source.content}</blockquote>{error&&<p role="alert">{error}</p>}{url?<a className="cp-button cp-secondary" href={url} target="_blank" rel="noreferrer">Open original file <ExternalLink size={16}/></a>:!error&&<LoaderCircle className="cp-spin"/>}<p className="cp-muted">Extracted text and model observations should be checked against the original.</p></section></div>;
}
