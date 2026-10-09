'use client';
import {Activity,FileText,ArrowUpRight} from 'lucide-react';
import type {Source} from '@/lib/pulse';
export function Badge({value}:{value:string}){return <span className={'cp-badge cp-'+value.toLowerCase().replaceAll(' ','-')}>{value}</span>;}
export function Empty({title,detail,action}:{title:string;detail:string;action?:React.ReactNode}){return <div className="cp-empty"><span className="cp-empty-icon"><Activity size={25}/></span><h3>{title}</h3><p>{detail}</p>{action}</div>;}
export function Sources({sources,onSelect}:{sources:Source[];onSelect:(source:Source)=>void}){return <div className="cp-citations">{sources.filter((source,i)=>sources.findIndex(item=>item.file_id===source.file_id)===i).map((source,i)=><button key={source.id} onClick={()=>onSelect(source)}><FileText size={13}/>{i+1}. {source.file_name}{source.page&&' · p.'+source.page}<ArrowUpRight size={12}/></button>)}</div>;}

