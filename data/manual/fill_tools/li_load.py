"""Street index for Long Island inside the city (Brooklyn + Queens), cached as a pickle."""
from zonelib import *
import time
t = time.time()
S = island_streets((-74.06, 40.535, -73.695, 40.815), 'Flatbush Avenue', 'Atlantic Avenue')
print('names', len(S.by), 'land ha %.0f' % (S.island.area / 1e4), 'secs %.0f' % (time.time() - t))
S.con = None
pickle.dump(S, open(os.path.join(INTERIM, 'li_streets.pkl'), 'wb'))
