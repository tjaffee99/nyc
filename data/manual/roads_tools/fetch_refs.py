"""Route numbers of the motorway / trunk segments (Overture `routes`: OpenStreetMap route relations — "I 80",
"NJ 17", "US 46" ...), which the pipeline's freeways.parquet does not carry. Outside the city most highways
have no name in Overture, only a number: hw_defs.py selects them with "ref:<number>" (make_routes.py).

  -> data/raw/roads/overture/freeway_refs.parquet   id, refs (list), networks (list)

Same release and box as pipeline/download_overture.py (common.OVERTURE_RELEASE, common.REGION_BBOX); cached.
Usage: ../../../.venv/bin/python fetch_refs.py [refetch]      (about 2 minutes, anonymous S3 read)
"""
import os
import sys

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from common import OVERTURE_RELEASE, REGION_BBOX  # noqa: E402

OUT = os.path.join(ROOT, "data", "raw", "roads", "overture", "freeway_refs.parquet")

if __name__ == "__main__":
    if os.path.exists(OUT) and "refetch" not in sys.argv[1:]:
        print("cached:", OUT)
        sys.exit(0)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='1500MB'")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2');")
    src = f"s3://overturemaps-us-west-2/release/{OVERTURE_RELEASE}/theme=transportation/type=segment/*"
    x0, y0, x1, y1 = REGION_BBOX
    con.execute(f"""
    COPY (
      SELECT id, [r.ref FOR r IN routes] AS refs, [r.network FOR r IN routes] AS networks
      FROM read_parquet('{src}', hive_partitioning=1)
      WHERE bbox.xmin < {x1} AND bbox.xmax > {x0} AND bbox.ymin < {y1} AND bbox.ymax > {y0}
        AND subtype = 'road' AND class IN ('motorway', 'trunk') AND routes IS NOT NULL
    ) TO '{OUT}.tmp' (FORMAT parquet);""")
    os.replace(OUT + ".tmp", OUT)
    print(con.execute(f"SELECT count(*) FROM '{OUT}'").fetchone()[0], "segments with route numbers ->", OUT)
