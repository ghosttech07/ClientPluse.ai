import PulseCustomer from '@/components/pulse-customer';
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <PulseCustomer id={id}/>;}
