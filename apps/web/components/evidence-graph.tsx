'use client';
import { useMemo,useState } from 'react';
import { ReactFlow,Background,Controls,MiniMap,useNodesState,useEdgesState,Node,Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
export type GraphData={nodes:{id:string;label:string;type:string;modality:string}[];edges:{id:string;source:string;target:string;label:string;evidence_id:string;inferred:boolean}[];limitations:string};
export default function EvidenceGraph({data,onSelect}:{data:GraphData;onSelect:(id:string)=>void}){
 const [search,setSearch]=useState(''),[filter,setFilter]=useState('All');
 const initial=useMemo(()=>{let sourceIndex=0,entityIndex=0;return data.nodes.map(n=>({id:n.id,position:{x:n.type==='source'?30:430,y:n.type==='source'?sourceIndex++*120:entityIndex++*85},data:{label:n.label},style:{background:n.type==='source'?'#13243b':'#153344',color:'#dce9f5',border:'1px solid #305a6c',borderRadius:12,width:240,padding:15},type:'default'}));},[data]);
 const [nodes,,onNodesChange]=useNodesState<Node>(initial);const [edges,,onEdgesChange]=useEdgesState<Edge>(data.edges.map(e=>({...e,style:{stroke:'#38a6bf'},labelStyle:{fill:'#678351',fontSize:11},labelBgStyle:{fill:'#f3f8eb'},animated:false})));
 const matches=new Set(data.nodes.filter(n=>n.label.toLowerCase().includes(search.toLowerCase())&&(filter==='All'||n.modality===filter)).map(n=>n.id));
 const shown=new Set(matches);if(search||filter!=='All')data.edges.forEach(e=>{if(matches.has(e.source)||matches.has(e.target)){shown.add(e.source);shown.add(e.target);}});
 return <><div className="graph-toolbar"><div className="search-box"><input aria-label="Search graph" placeholder="Find a source or entity…" value={search} onChange={e=>setSearch(e.target.value)}/></div><select aria-label="Filter graph modality" value={filter} onChange={e=>setFilter(e.target.value)}><option>All</option>{Array.from(new Set(data.nodes.map(n=>n.modality))).map(m=><option key={m}>{m}</option>)}</select><span className="muted">{shown.size} nodes</span></div><div className="graph-canvas"><ReactFlow nodes={nodes.map(n=>({...n,hidden:!shown.has(n.id)}))} edges={edges.map(e=>({...e,hidden:!shown.has(e.source)||!shown.has(e.target)}))} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} fitView colorMode="light" onNodeClick={(_,n)=>onSelect(n.id)} onEdgeClick={(_,e)=>{const edge=data.edges.find(x=>x.id===e.id);if(edge)onSelect(edge.evidence_id);}}><Background color="#dce8ce" gap={24}/><Controls/><MiniMap nodeColor="#387488"/></ReactFlow></div></>;
}
