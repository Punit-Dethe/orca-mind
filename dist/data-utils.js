export function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
export function formatNumber(n){return Number(n).toLocaleString('en-US',{maximumFractionDigits:2})}
export function filterCube(cube,filter){return cube.filter(x=>Object.entries(filter).every(([k,v])=>!v||x[k]===v))}
export function aggregate(rows,key){const m=new Map();for(const r of rows)m.set(r[key],(m.get(r[key])||0)+r.count);return [...m].map(([name,count])=>({name,count}))}
export function csvText(rows,columns,provenance={}){const cols=[...columns,...Object.keys(provenance)];const cell=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'};return [cols.map(cell).join(','),...rows.map(r=>cols.map(k=>cell(k in provenance?provenance[k]:r[k])).join(','))].join('\r\n')}
