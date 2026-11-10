"""Parse the OSM extracts: supports, towers, bridge outlines, bridge ways. Saves a pickle per file."""
import xml.etree.ElementTree as ET, glob, os, pickle, math, sys
RAW='data/raw/landmarks_bridges'
def load(fn):
    nodes={}; ways={}; rels={}
    for ev,el in ET.iterparse(fn):
        if el.tag=='node':
            tags={t.get('k'):t.get('v') for t in el.findall('tag')}
            nodes[el.get('id')]=(float(el.get('lon')),float(el.get('lat')),tags)
            el.clear()
        elif el.tag=='way':
            tags={t.get('k'):t.get('v') for t in el.findall('tag')}
            ways[el.get('id')]=([n.get('ref') for n in el.findall('nd')],tags)
            el.clear()
        elif el.tag=='relation':
            tags={t.get('k'):t.get('v') for t in el.findall('tag')}
            rels[el.get('id')]=([(m.get('type'),m.get('ref'),m.get('role')) for m in el.findall('member')],tags)
            el.clear()
    return nodes,ways,rels
def summ(fn):
    nodes,ways,rels=load(fn)
    key=os.path.basename(fn)[4:-4]
    out={'nodes':[], 'ways':[], 'bridgeways':[]}
    def geom(refs): return [(nodes[r][0],nodes[r][1]) for r in refs if r in nodes]
    for i,(x,y,t) in nodes.items():
        if 'bridge:support' in t or t.get('man_made') in('bridge_support','tower','pylon') :
            out['nodes'].append((i,x,y,t))
    for i,(refs,t) in ways.items():
        g=geom(refs)
        if not g: continue
        interesting = ('bridge:support' in t or t.get('man_made') in('bridge','bridge_support','tower','pier_support') or t.get('building')=='bridge'
                       or 'bridge' in (t.get('name','')+t.get('description','')).lower() and ('building' in t or 'building:part' in t or 'man_made' in t)
                       or t.get('tower:type')=='bridge')
        if interesting: out['ways'].append((i,g,t))
        if t.get('bridge') not in (None,'no') and ('highway' in t or 'railway' in t):
            out['bridgeways'].append((i,g,t))
    out['rels']=[(i,m,t) for i,(m,t) in rels.items() if t.get('man_made')=='bridge' or t.get('type')=='bridge']
    pickle.dump(out,open(f'data/interim/landmarks_bridges/osm_{key}.pkl','wb'))
    return key,out
def cen(g):
    xs=[p[0] for p in g]; ys=[p[1] for p in g]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
    k=111320*math.cos(math.radians(cy))
    return cx,cy,(max(xs)-min(xs))*k,(max(ys)-min(ys))*110574
if __name__=='__main__':
    for fn in sorted(glob.glob(RAW+'/osm_*.osm')):
        if len(sys.argv)>1 and not any(a in fn for a in sys.argv[1:]): continue
        key,o=summ(fn)
        print('=====',key, 'support nodes',len(o['nodes']),'ways',len(o['ways']),'bridgeways',len(o['bridgeways']),'rels',len(o['rels']))
        for i,x,y,t in o['nodes'][:60]:
            print('  N',i,round(x,6),round(y,6),{k:v for k,v in t.items() if k in('bridge:support','man_made','name','height','ele')})
        for i,g,t in o['ways']:
            cx,cy,w,h=cen(g)
            print('  W',i,round(cx,6),round(cy,6),f'{w:.0f}x{h:.0f}m',{k:v for k,v in t.items() if k in('bridge:support','man_made','name','height','building','building:part','bridge:structure','tower:type','min_height','layer')})
        for i,m,t in o['rels']:
            print('  R',i,len(m),{k:v for k,v in t.items() if k in('name','man_made','type','bridge:structure','height','length','wikidata')})
        names={}
        for i,g,t in o['bridgeways']:
            k=(t.get('name'),t.get('bridge:name'),t.get('highway') or 'rail:'+t.get('railway',''),t.get('bridge:structure'),t.get('bridge'))
            names[k]=names.get(k,0)+1
        for k,v in sorted(names.items(),key=lambda kv:-kv[1])[:14]: print('  BW',v,k)
