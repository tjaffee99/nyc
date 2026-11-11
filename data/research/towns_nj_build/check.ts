import {MeshBuilder} from '/home/user/nyc/viewer/src/landmarks/kit';
import {NJ_TOWNS} from '/home/user/nyc/viewer/src/landmarks/nj-towns';
const out:any[]=[];
for (const lm of NJ_TOWNS) {
  const b=new MeshBuilder(); lm.build(b); const m=b.build(); const p=m.positions.value;
  let zmax=-1e9, zmin=1e9, bad=0;
  for(let i=0;i<p.length;i+=3){ if(!isFinite(p[i])||!isFinite(p[i+1])||!isFinite(p[i+2])) bad++; zmax=Math.max(zmax,p[i+2]); zmin=Math.min(zmin,p[i+2]);}
  // plan area by rasterizing triangles at 0.5 m
  const g=0.5; const set=new Set<number>(); const cells=new Map<number,[number,number]>(); 
  let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  for(let i=0;i<p.length;i+=3){x0=Math.min(x0,p[i]);x1=Math.max(x1,p[i]);y0=Math.min(y0,p[i+1]);y1=Math.max(y1,p[i+1]);}
  for(let t=0;t<p.length;t+=9){
    const ax=p[t],ay=p[t+1],bx=p[t+3],by=p[t+4],cx=p[t+6],cy=p[t+7];
    const mnx=Math.floor(Math.min(ax,bx,cx)/g),mxx=Math.ceil(Math.max(ax,bx,cx)/g),mny=Math.floor(Math.min(ay,by,cy)/g),mxy=Math.ceil(Math.max(ay,by,cy)/g);
    const d=(bx-ax)*(cy-ay)-(cx-ax)*(by-ay); if(Math.abs(d)<1e-9) continue;
    for(let i=mnx;i<=mxx;i++)for(let j=mny;j<=mxy;j++){const x=(i+.5)*g,y=(j+.5)*g;
      const u=((x-ax)*(cy-ay)-(cx-ax)*(y-ay))/d, v=((bx-ax)*(y-ay)-(x-ax)*(by-ay))/d;
      if(u>=0&&v>=0&&u+v<=1) {set.add(i*100000+j); cells.set(i*100000+j,[x,y]);}}
  }
  const rep=(lm.replaces??[]).map(r=>{let a=0;for(let i=0;i<r.length;i++){const q=r[(i+1)%r.length];a+=r[i][0]*q[1]-q[0]*r[i][1];}return Math.abs(a)/2;}).reduce((a,b)=>a+b,0);
  let outside=0;
  if(lm.replaces&&lm.replaces.length){ const inP=(x:number,y:number)=>lm.replaces!.some(r=>{let c=false;for(let i=0,j=r.length-1;i<r.length;j=i++){if(((r[i][1]>y)!==(r[j][1]>y))&&(x<(r[j][0]-r[i][0])*(y-r[i][1])/(r[j][1]-r[i][1])+r[i][0]))c=!c;}return c;});
    for(const [x,y] of cells.values()) if(!inP(x,y)) outside++; }
  out.push({id:lm.id,verts:p.length/3,top:+zmax.toFixed(2),zmin:+zmin.toFixed(2),plan:Math.round(set.size*g*g),replaced:Math.round(rep),outsideM2:Math.round(outside*g*g),bad});
}
console.table(out);
