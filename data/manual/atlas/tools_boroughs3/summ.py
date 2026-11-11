"""per-plate summary of the work pickles: python -I summ.py <layer>"""
import pickle,sys,glob,os,json
L=sys.argv[1]
W=f'data/interim/atlas_boroughs3/{L}'
spec=json.load(open('data/manual/atlas/tools_boroughs3/layers.json'))[L]
sh={str(p['id']):p['sheet'] for p in spec['plates']}
print('plate sheet n coincide off_m corrected gcps cv_rms')
for f in sorted(glob.glob(W+'/*.pkl')):
    st=pickle.load(open(f,'rb'))['stats']; pid=os.path.basename(f)[:-4]
    print(pid,sh.get(pid),st['n'],st.get('coincide'),st.get('off_median_m'),st.get('corrected'),st.get('gcps'),st.get('cv_rms'),st.get('mpp'),sep='\t')
