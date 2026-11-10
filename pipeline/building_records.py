"""Stage: recorded construction and demolition dates from official datasets.

Not estimates: every date written here is a field of a city record, joined to the city's
footprints by Building Identification Number (BIN). Sources, fields, licences, row counts
and the rules for choosing between records: data/research/building_records.md.

  python building_records.py download     # fetch the raw tables into data/raw/records/ (cached)
  python building_records.py              # download + normalise + write the outputs

Inputs
  data/raw/records/*.csv                   NYC Open Data extracts (see SOURCES below)
  data/interim/nyc_footprints_raw.parquet  today's footprints (BIN, assessor year, outline)
  data/interim/nyc_buildings.parquet       the built buildings (what year the pipeline has now)

Outputs
  data/tables/known_building_dates.records.csv          standing buildings: recorded year by BIN
  data/manual/demolished/demolished_footprints.geojson  vanished buildings with their real outlines
  data/manual/demolished/flagged.csv                    historic outlines NOT written, and why
  data/interim/records/*.parquet, report.json           normalised records and the numbers quoted
                                                        in data/research/building_records.md
"""
from __future__ import annotations

import sys
import time
from urllib.parse import urlencode

from common import INTERIM, MANUAL, RAW, TABLES, log, session

SODA = "https://data.cityofnewyork.us"
REC = RAW / "records"
WORK = INTERIM / "records"
OUT_KNOWN = TABLES / "known_building_dates.records.csv"
OUT_DEMO = MANUAL / "demolished" / "demolished_footprints.geojson"
OUT_FLAG = MANUAL / "demolished" / "flagged.csv"
TODAY = 2026.86  # the day this stage was written (2026-11-10); dates after it are typos


def soda(dataset: str, select: str | None = None, where: str | None = None, order: str | None = None) -> str:
    q = {"$limit": 5000000}
    if select:
        q["$select"] = select
    if where:
        q["$where"] = where
    if order:
        q["$order"] = order
    return f"{SODA}/resource/{dataset}.csv?{urlencode(q)}"


def page(dataset: str) -> str:
    return f"{SODA}/d/{dataset}"


# name -> (file under data/raw/records, download URL, landing page quoted as source_url)
SOURCES = {
    # OTI: outlines of buildings demolished or significantly altered, with construction and demolition year
    "historic": ("building_historic.csv", f"{SODA}/api/views/ipkp-snf6/rows.csv?accessType=DOWNLOAD", page("ipkp-snf6")),
    # NYCHA: completion date per development; BIN per residential building
    "nycha_book": ("nycha_development_data_book.csv", soda("evjd-dqpz"), page("evjd-dqpz")),
    "nycha_addr": ("nycha_residential_addresses.csv", soda("3ub5-4ph8"), page("3ub5-4ph8")),
    # DOB BIS job filings: new-building and demolition jobs (1989 ->)
    "dob_jobs": ("dob_jobs_nb_dm.csv", soda(
        "ic3t-wcy2",
        "job__,doc__,borough,house__,street_name,block,lot,bin__,job_type,job_status,latest_action_date,building_type,"
        "pre__filing_date,approved,fully_permitted,signoff_date,existingno_of_stories,proposed_no_of_stories,"
        "existing_height,proposed_height,existing_occupancy,proposed_occupancy,existing_dwelling_units,"
        "proposed_dwelling_units,building_class,job_description,gis_latitude,gis_longitude",
        "job_type in ('NB','DM')"), page("ic3t-wcy2")),
    # DOB NOW job filings (2016 ->)
    "dobnow_jobs": ("dobnow_jobs_nb_dm.csv", soda(
        "w9ak-ipjd",
        "job_filing_number,filing_status,house_no,street_name,borough,block,lot,bin,building_type,existing_stories,"
        "existing_height,proposed_no_of_stories,proposed_height,filing_date,current_status_date,first_permit_date,"
        "approved_date,signoff_date,job_type,latitude,longitude,bbl,job_description",
        "job_type in ('New Building','Full Demolition','ALT-CO - New Building with Existing Elements to Remain')"),
        page("w9ak-ipjd")),
    # certificates of occupancy (BIS: July 2012 ->; DOB NOW: 2021 ->)
    "dob_co": ("dob_co_nb.csv", soda(
        "bs8b-p36w", "job_number,job_type,c_o_issue_date,bin_number,issue_type,borough,block,lot,latitude,longitude",
        "job_type='NB'"), page("bs8b-p36w")),
    "dobnow_co": ("dobnow_co_nb.csv", soda(
        "pkdm-hqz6", "job_filing_name,job_type,bin,borough,block,lot,c_of_o_status,c_of_o_filing_type,"
        "c_of_o_issuance_date,latitude,longitude,bbl",
        "upper(job_type) like '%NEW BUILDING%'"), page("pkdm-hqz6")),
    # permits: the first new-building / demolition permit of a job (BIS; 1989-2013 and 2013 ->)
    "permits_hist": ("dob_permits_hist_nb_dm.csv", soda(
        "bty7-2jhb", "job,job_type,bin,block,lot,borough,permit_type,permit_status,filing_status,permit_sequence,"
        "issuance_date,job_start_date",
        "(job_type='NB' and permit_type='NB') or (job_type='DM' and permit_type='DM')"), page("bty7-2jhb")),
    "permits": ("dob_permits_nb_dm.csv", soda(
        "ipu4-2q9a", "job__,job_type,bin__,block,lot,borough,permit_type,permit_status,filing_status,"
        "permit_sequence__,issuance_date,job_start_date",
        "(job_type='NB' and permit_type='NB') or (job_type='DM' and permit_type='DM')"), page("ipu4-2q9a")),
    # DCP Housing Database: residential new buildings, alterations, demolitions completed 2010 ->
    "housing_db": ("housing_db.csv", soda(
        "br6q-ssj3", "job_number,job_type,job_status,compltyear,permityear,classainit,classaprop,boro,bin,bbl,"
        "addressnum,addressst,datefiled,datepermit,datelstupd,datecomplt,floorsinit,floorsprop,latitude,longitude"),
        page("br6q-ssj3")),
    # HPD: affordable housing production by building (2014 ->)
    "hpd": ("hpd_affordable_by_building.csv", soda(
        "hg8x-zxpr", "project_id,project_name,building_id,house_number,street_name,borough,bbl,bin,latitude,longitude,"
        "project_start_date,project_completion_date,building_completion_date,reporting_construction_type,total_units"),
        page("hg8x-zxpr")),
    # NYC Parks structures (construction / demolition year per structure)
    "parks": ("parks_structures.csv", soda(
        "n8q6-i44s", "alteration_year,bbl,bin,borough,construction_year,description,doitt_id,doitt_source,"
        "demolition_year,gispropnum,height_roof,location,featurestatus"), page("n8q6-i44s")),
    # Local Law 84 benchmarking: owner-reported year built of large buildings, incl. city property
    "ll84": ("ll84_2023_present.csv", soda(
        "5zyy-y8am", "report_year,property_id,property_name,parent_property_id,nyc_borough_block_and_lot,"
        "nyc_building_identification,address_1,primary_property_type_self,year_built,construction_status,"
        "number_of_buildings"), page("5zyy-y8am")),
    # DOF assessment rolls FY2010 and FY2017 (the last with the field): year built with the assessor's own
    # "estimated" flag, per tax lot (tax class 1; tax classes 2-4)
    "dof_tc1_2017": ("dof_roll_tc1_2017.csv", soda(
        "m8p6-tp4b", "bble,ease,year4,txcl,bldgcl,story,bldgs,yrb,yrb_flag,yrb_rng,yra1,yra2", "year4=2017"),
        page("m8p6-tp4b")),
    "dof_tc234_2017": ("dof_roll_tc234_2017.csv", soda(
        "kevu-8hby", "bble,ease,year4,txcl,bldgcl,story,bldgs,yrb,yrb_flag,yrb_rng,yra1,yra2", "year4=2017"),
        page("kevu-8hby")),
    "dof_tc1_2010": ("dof_roll_tc1_2010.csv", soda(
        "m8p6-tp4b", "bble,ease,year4,bldgcl,story,bldgs,yrb,yrb_flag,yrb_rng", "year4=2010"), page("m8p6-tp4b")),
    "dof_tc234_2010": ("dof_roll_tc234_2010.csv", soda(
        "kevu-8hby", "bble,ease,year4,bldgcl,story,bldgs,yrb,yrb_flag,yrb_rng", "year4=2010"), page("kevu-8hby")),
    # HPD: legal class of multiple dwellings (old law / new law tenement, erected before / after 1929)
    "hpd_buildings": ("hpd_buildings.csv", soda(
        "kj4p-ruqc", "buildingid,boroid,block,lot,bin,housenumber,streetname,dobbuildingclass,legalstories,"
        "lifecycle,recordstatus"), page("kj4p-ruqc")),
}


def fetch(name: str):
    rel, url, _ = SOURCES[name]
    path = REC / rel
    if path.exists() and path.stat().st_size > 0:
        log(f"{name}: cached ({path.stat().st_size / 1e6:.1f} MB)")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    s = session()
    for attempt in range(5):
        try:
            t0 = time.time()
            with s.get(url, stream=True, timeout=900) as r:
                r.raise_for_status()
                n = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        n += len(chunk)
            tmp.rename(path)
            log(f"{name}: {n / 1e6:.1f} MB in {time.time() - t0:.0f} s -> {path}")
            return path
        except Exception as e:  # noqa: BLE001 - network errors of any kind are retried
            log(f"{name}: {e!r} (attempt {attempt + 1})")
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {name}")


def download():
    for n in SOURCES:
        fetch(n)


# ------------------------------------------------------------------ helpers
def db():
    import duckdb
    c = duckdb.connect()
    c.execute("set memory_limit='1500MB'")
    c.execute("set threads=4")
    return c


def csv(name: str) -> str:
    return f"read_csv('{REC / SOURCES[name][0]}', all_varchar=true, header=true)"


def url(name: str) -> str:
    return SOURCES[name][2]


# a date column: ISO, "MM/DD/YYYY ..." or "MM/DD/YY hh:mm:ss AM"
def D(col: str) -> str:
    return (f"coalesce(try_cast({col} as timestamp), case when substr({col}, 9, 1) = ' ' "
            f"then try_strptime(substr({col}, 1, 8), '%m/%d/%y') else try_strptime(substr({col}, 1, 10), '%m/%d/%Y') end)")


DEC = "(year({0}) + (dayofyear({0}) - 1) / 365.25)"  # decimal year of a timestamp


def find_heaps(year, boro):
    """nyc_buildings.find_heaps (copied so this stage does not import the heavy one): placeholder
    years per borough = a count more than 3x the median of the non-round years within +/- 4."""
    import numpy as np
    heaps = {}
    for b in np.unique(boro):
        y = year[(boro == b) & np.isfinite(year)].astype(int)
        cnt = dict(zip(*np.unique(y, return_counts=True)))
        flagged: set[int] = set()
        for rnd in (True, False, False):
            for v in sorted(cnt):
                if v > 1990 or v in flagged or (v % 5 == 0) != rnd or cnt[v] < 300:
                    continue
                nb = [cnt.get(u, 0) for u in range(v - 4, v + 5) if u != v and u % 5 and u not in flagged]
                if nb and cnt[v] > 3 * max(float(np.median(nb)), 1.0):
                    flagged.add(v)
        heaps[b] = flagged
    return heaps


# ------------------------------------------------------------------ today's buildings
def load_today(c):
    """fp: today's footprints (one row per BIN: the largest outline); pipe: what the pipeline has."""
    c.execute(f"""create table fp as
        select bin, arg_max(cast(doitt_id as varchar), height_m) doitt_id, max(year_raw) year_raw,
               arg_max(feature_code, height_m) fc, max(height_m) height_m, arg_max(lon, height_m) lon,
               arg_max(lat, height_m) lat, any_value(base_bbl) bbl, any_value(name) fp_name, count(*) n_fp
        from '{INTERIM / "nyc_footprints_raw.parquet"}'
        where bin is not null and bin % 1000000 <> 0 group by 1""")
    b = INTERIM / "nyc_buildings.parquet"
    if b.exists():
        c.execute(f"""create table pipe as
            select cast(bin as bigint) bin, arg_max(start_year, area) p_year, arg_max(year_src, area) p_src,
                   arg_max(year_confidence, area) p_conf, arg_max(raw_year, area) p_raw, any_value(boro) boro,
                   arg_max(name, area) p_name, arg_max(bldgclass, area) bldgclass, sum(area) area
            from '{b}' where end_year = 9999 and bin is not null group by 1""")
    else:  # first build: nothing to compare with, every record is written
        c.execute("""create table pipe as select bin, cast(null as double) p_year, 'none' p_src, 'estimated' p_conf,
                     cast(year_raw as double) p_raw, substr(cast(bin as varchar), 1, 1) boro, fp_name p_name,
                     cast(null as varchar) bldgclass, cast(null as double) area from fp""")
    n = c.execute("select count(*) from fp").fetchall()[0][0]
    log(f"records: {n} BINs in today's footprints")


def heap_sets(c):
    """Placeholder years per borough, as the pipeline found them (else recomputed)."""
    import numpy as np
    t = c.execute("select distinct boro, cast(p_raw as int) y from pipe where p_src like 'heap%'").df()
    if len(t):
        return {b: set(g.y) for b, g in t.groupby("boro")}
    t = c.execute("select substr(cast(bin as varchar), 1, 1) boro, year_raw y from fp where year_raw > 1600").df()
    return find_heaps(t.y.values.astype(float), t.boro.values)


# ------------------------------------------------------------------ DOB jobs
def norm_dob(c):
    """nb: one row per new-building job with its recorded completion; dm: per demolition job."""
    c.execute(f"""create table bis as
        select "job__" job, any_value(job_type) jt, max(try_cast("bin__" as bigint)) bin, max(job_status) st,
               max({D('signoff_date')}) signoff, min({D('"pre__filing_date"')}) filed,
               min({D('fully_permitted')}) permitted,
               max(try_cast(proposed_no_of_stories as int)) pst, max(try_cast(proposed_height as double)) ph,
               max(try_cast(existingno_of_stories as int)) est, max(try_cast(existing_height as double)) eh,
               arg_min(proposed_occupancy, "doc__") pocc, arg_min(job_description, "doc__") descr,
               any_value(borough) boro, any_value(block) block, any_value(lot) lot,
               any_value("house__") house, any_value(street_name) street,
               max(try_cast(gis_latitude as double)) lat, max(try_cast(gis_longitude as double)) lon
        from {csv('dob_jobs')} group by 1""")
    c.execute(f"""create table now as
        select split_part(job_filing_number, '-', 1) job,
               case when any_value(job_type) = 'Full Demolition' then 'DM' else 'NB' end jt,
               any_value(job_type) jt_long, max(try_cast(bin as bigint)) bin, max(filing_status) st,
               max({D('signoff_date')}) signoff, min({D('filing_date')}) filed, min({D('first_permit_date')}) permitted,
               max(try_cast(proposed_no_of_stories as int)) pst, max(try_cast(proposed_height as double)) ph,
               max(try_cast(existing_stories as int)) est, max(try_cast(existing_height as double)) eh,
               cast(null as varchar) pocc, arg_min(job_description, job_filing_number) descr,
               any_value(borough) boro, any_value(block) block, any_value(lot) lot,
               any_value(house_no) house, any_value(street_name) street,
               max(try_cast(latitude as double)) lat, max(try_cast(longitude as double)) lon
        from {csv('dobnow_jobs')} group by 1""")
    # first permit of the job (new-building permit / demolition permit)
    c.execute(f"""create table permit as select job, min(d) first_permit from (
        select job, {D('issuance_date')} d from {csv('permits_hist')}
        union all select "job__", {D('issuance_date')} from {csv('permits')}) where d is not null group by 1""")
    # first certificate of occupancy of the job
    c.execute(f"""create table co as select job, min(d) first_co from (
        select job_number job, {D('c_o_issue_date')} d from {csv('dob_co')}
        union all select split_part(job_filing_name, '-', 1), {D('c_of_o_issuance_date')} from {csv('dobnow_co')}
        ) where d is not null and d < timestamp '2026-11-11' group by 1""")
    c.execute(f"""create table hdb as select job_number job, min(try_cast(datecomplt as timestamp)) dc
        from {csv('housing_db')} where job_type = 'New Building' and datecomplt is not null group by 1""")
    c.execute("""create table jobs as
        select 'bis' sys, job, jt, bin, st, signoff, filed, permitted, pst, ph, est, eh, pocc, descr, boro, block, lot, house, street, lat, lon from bis
        union all
        select 'now', job, jt, bin, st, signoff, filed, permitted, pst, ph, est, eh, pocc, descr, boro, block, lot, house, street, lat, lon
        from now where jt_long <> 'ALT-CO - New Building with Existing Elements to Remain'""")
    # completion of a new-building job: the first certificate of occupancy where the open data can know it
    # (DCP's Housing Database carries it for residential jobs completed since 2010; the certificate tables
    # start in July 2012, so they are trusted only for jobs permitted from July 2011), else the sign-off
    c.execute("""create table nb as
        with a as (
          select j.*, least(j.permitted, p.first_permit) permit, h.dc, co.first_co
          from jobs j left join permit p using (job) left join hdb h using (job) left join co using (job)
          where j.jt = 'NB' and j.bin is not null and j.bin % 1000000 <> 0),
        b as (
          select *, case when dc is not null then dc
                         when first_co is not null and coalesce(permit, filed) >= timestamp '2011-07-01' then first_co
                    end co_date from a)
        select *, case when co_date is not null and (signoff is null or co_date <= signoff) then co_date else signoff end done,
                  case when co_date is not null and (signoff is null or co_date <= signoff)
                       then (case when dc is not null then 'first_co_hdb' else 'first_co' end) else 'signoff' end kind
        from b""")
    c.execute("delete from nb where done is null or done > timestamp '2026-11-11' or (permit is not null and done < permit)")
    c.execute("""create table dm as
        select j.*, p.first_permit from jobs j left join permit p using (job)
        where j.jt = 'DM' and j.bin is not null and j.bin % 1000000 <> 0""")
    r = c.execute("select kind, count(*), count(distinct bin) from nb group by 1 order by 1").fetchall()
    log(f"records: completed new-building jobs {r}")
    r2 = c.execute("select count(*), count(signoff), count(first_permit), count(distinct bin) from dm").fetchall()[0]
    log(f"records: demolition jobs {r2[0]} (signed off {r2[1]}, permit {r2[2]}), {r2[3]} BINs")
    return {"nb_jobs_completed": {k: [n, b] for k, n, b in r}, "dm_jobs": r2[0], "dm_signed_off": r2[1], "dm_bins": r2[3]}


GARAGE_OCC = ("B-2", "U", "S-2", "K", "B-1")


def dob_candidates(c):
    """Per BIN of today's footprints: the completed new-building job that matches the building
    (proposed height against the measured roof height), the latest if several."""
    c.execute(f"""create table nbc as
        select nb.*, fp.height_m, fp.fc,
               case when nb.ph > 0 and fp.height_m > 0 then nb.ph * 0.3048 / fp.height_m
                    when nb.pst > 0 and fp.height_m > 0 then nb.pst * 3.3 / fp.height_m end ratio,
               (coalesce(nb.pocc, '') in {GARAGE_OCC} and (coalesce(nb.ph, 99) <= 15 or coalesce(nb.pst, 9) <= 1)
                or regexp_matches(lower(coalesce(nb.descr, '')), 'garage|car ?port|shed|fence|retaining wall|pool|deck'))
                and coalesce(nb.pst, 0) <= 1 as small_job
        from nb join fp using (bin)""")
    c.execute("""create table nbbest as
        select * from (
          select *, (ratio between 0.55 and 1.5) and not (small_job and coalesce(fc, 2100) <> 5110 and height_m > 4.5) ok,
                 row_number() over (partition by bin order by
                     ((ratio between 0.55 and 1.5) and not (small_job and coalesce(fc, 2100) <> 5110 and height_m > 4.5)) desc,
                     done desc) rn
          from nbc) where rn = 1""")
    r = c.execute("select ok, count(*) from nbbest group by 1").fetchall()
    log(f"records: BINs with a completed new-building job: {dict(r)} (True = the job fits the footprint)")
    return {"nb_bins_fit": dict(r).get(True, 0), "nb_bins_misfit": sum(n for k, n in r if not k)}


# ------------------------------------------------------------------ standing buildings
def standing_records(c, rep):
    """known_building_dates.records.csv: recorded years of standing buildings, by BIN.

    Evidence order when several records exist for one BIN: NYCHA's completion date of a newly built
    development > the first certificate of occupancy of a DOB new-building job > the job's sign-off
    > the owner-reported year of the Local Law 84 benchmarking filings (marked estimated).
    A record is written when the pipeline has no recorded year for the building (placeholder
    "heap" year, a neighbours' estimate, nothing), or when the assessor's year contradicts it:
    the assessor's year predates the job's permit (a previous building's year), or the first
    certificate of occupancy came two or more years after it. Sign-offs that are merely later than
    an assessor's year lying between permit and sign-off are NOT written (a sign-off can trail the
    building by years); rows the Landmarks Commission dates are left alone. Everything, written or
    not, is in data/interim/records/records_by_bin.parquet with the decision taken."""
    import numpy as np
    import pandas as pd

    # --- DOB
    d = c.execute(f"""select n.bin, n.sys, n.job, n.kind, {DEC.format('n.done')} y, year(n.done) ry,
               strftime(n.done, '%Y-%m-%d') done, year(coalesce(n.permit, n.filed)) py,
               strftime(coalesce(n.permit, n.filed), '%Y-%m-%d') permit, n.pst, n.ph, n.ratio
        from nbbest n where n.ok""").df()
    d = _f(d)
    d["src"] = "dob"
    d["source_url"] = np.where(d.kind == "first_co_hdb", url("housing_db"),
                               np.where(d.sys == "now", url("dobnow_jobs"), url("dob_jobs")))
    what = d.kind.map({"first_co_hdb": "first certificate of occupancy (DCP Housing Database)",
                       "first_co": "first certificate of occupancy", "signoff": "job signed off"})
    d["what"] = ("DOB new-building job " + d.job + ": " + what + " " + d.done
                 + np.where(d.permit.notna(), "; permit " + d.permit.fillna(""), ""))
    d["rid"] = "dob-" + d.job

    # --- NYCHA: completion date of the development, for developments built new
    n = c.execute(f"""select try_cast(a.bin as bigint) bin, any_value(a.development) dev, any_value(a.tds) tds,
               any_value(b.type) typ, any_value(try_cast(b.completion_date as timestamp)) cd
        from {csv('nycha_addr')} a join {csv('nycha_book')} b on try_cast(b."tds_" as int) = try_cast(a.tds as int)
        group by 1""").df()
    n = _f(n)
    rep["nycha_bins"] = int(len(n))
    rep["nycha_bins_rehab_skipped"] = int((~n.typ.fillna("").str.startswith("NEW")).sum())
    n = n[n.typ.fillna("").str.startswith("NEW") & n.cd.notna() & n.bin.notna()].copy()
    n["y"] = n.cd.dt.year + (n.cd.dt.day_of_year - 1) / 365.25
    n["ry"] = n.cd.dt.year
    n["kind"] = "nycha"
    n["src"] = "nycha"
    n["source_url"] = url("nycha_book")
    n["what"] = ("NYCHA Development Data Book: " + n.dev.str.title() + " (TDS " + n.tds.astype(str)
                 + ") completed " + n.cd.dt.strftime("%Y-%m-%d") + " (date of the whole development)")
    n["rid"] = "nycha-" + n.tds.astype(str) + "-" + n.bin.astype("int64").astype(str)
    n["rname"] = "NYCHA " + n.dev.str.title()

    # --- Local Law 84: owner-reported year built, single-building properties with one BIN
    l = c.execute(f"""select try_cast(trim(nyc_building_identification) as bigint) bin,
               max(try_cast(year_built as int)) yb, min(try_cast(year_built as int)) yb_mode,
               max(property_name) pn, max(primary_property_type_self) pt,
               max(report_year) ryr
        from {csv('ll84')} where number_of_buildings = '1'
          and try_cast(trim(nyc_building_identification) as bigint) is not null group by 1""").df()
    l = _f(l)
    rep["ll84_single_bin_properties"] = int(len(l))
    l = l[(l.yb == l.yb_mode) & l.yb.between(1800, 2026)].copy()
    l["y"] = l.yb.astype(float)
    l["ry"] = l.yb.astype(int)
    l["kind"] = "ll84"
    l["src"] = "ll84"
    l["source_url"] = url("ll84")
    l["what"] = ("Local Law 84 benchmarking filing " + l.ryr.astype(str) + " (" + l.pt.fillna("") + "): year built "
                 + l.yb.astype(int).astype(str) + " as reported by the owner - estimated")
    l["rid"] = "ll84-" + l.bin.astype("int64").astype(str)

    cols = ["bin", "src", "kind", "y", "ry", "rid", "source_url", "what"]
    allr = pd.concat([n[cols + ["rname"]], d[cols + ["py"]], l[cols]], ignore_index=True)
    allr["bin"] = allr.bin.astype("int64")
    t = c.execute("select fp.bin, fp.bbl, fp.lon, fp.lat, fp.fp_name, fp.height_m, p.* exclude (bin) from fp join pipe p using (bin)").df()
    t = _f(t)
    allr = allr.merge(t, on="bin", how="inner")
    rep["records_matched_to_footprints"] = allr.groupby("src").bin.nunique().to_dict()

    # corroboration for records that contradict the year on the lot by more than ten years: PLUTO's
    # year agrees with the record, or OTI's historic layer has a demolition on the lot before it
    pl = RAW / "nyc" / "pluto_lots.csv"
    pluto = c.execute(f"""select split_part(bbl, '.', 1) bbl, max(try_cast(yearbuilt as int)) pluto_year
        from read_csv('{pl}', all_varchar=true, header=true) group by 1""").df() if pl.exists() else \
        pd.DataFrame({"bbl": [], "pluto_year": []})
    demo = c.execute(f"""select "BASE_BBL" bbl, min(try_cast("DEMOLITION YEAR" as int)) first_demolition
        from {csv('historic')} where "LAST_STATUS_TYPE" = 'Demolition' and try_cast("DEMOLITION YEAR" as int) > 0
        group by 1""").df()
    allr = allr.merge(pluto, on="bbl", how="left").merge(demo, on="bbl", how="left")
    confirmed = ((allr.pluto_year - allr.ry).abs() <= 2) | (allr.first_demolition <= allr.ry + 1)

    strong = (allr.p_src == "assessor") & (allr.p_conf == "exact") & (allr.p_raw > 0)
    lpc = allr.p_src.isin(["lpc", "known"])
    diff = allr.ry - allr.p_raw
    dob = allr.src == "dob"
    dec = pd.Series("", index=allr.index)
    dec[~strong & ~lpc] = "write:no_recorded_year"
    # a new-building job on a lot whose (placeholder) year is far older: the job may be another structure
    far = dob & ~strong & ~lpc & (allr.p_raw > 0) & ((allr.ry - allr.p_year).abs() > 10)
    dec[far & confirmed] = "write:replaced_building"
    dec[far & ~confirmed] = "skip:unconfirmed_new_building"
    dec[lpc] = "skip:lpc"
    dec[strong & (diff.abs() <= 1)] = "skip:agrees"
    later = strong & dob & (diff >= 2) & (diff <= 10)
    dec[later & allr.kind.str.startswith("first_co")] = "write:first_co_later"
    dec[later & (allr.kind == "signoff")] = "skip:signoff_later"
    dec[strong & dob & (diff > 10) & confirmed] = "write:replaced_building"
    dec[strong & dob & (diff > 10) & ~confirmed] = "skip:unconfirmed_new_building"
    dec[strong & dob & (diff <= -2)] = "skip:assessor_later"
    dec[strong & (allr.src == "nycha") & (diff.abs() >= 2)] = "write:nycha_differs"
    dec[strong & (allr.src == "ll84") & (diff.abs() >= 2)] = "skip:ll84_vs_assessor"
    # Local Law 84: only where it says something the placeholder year does not, and not a post-1988
    # year without a new-building job (those are mostly renovation years)
    ll = allr.src == "ll84"
    dec[ll & dec.str.startswith("write") & (allr.ry == allr.p_raw)] = "skip:ll84_repeats_placeholder"
    dec[ll & dec.str.startswith("write") & (allr.ry >= 1989)] = "skip:ll84_recent_without_job"
    allr["decision"] = dec
    # one row per BIN: NYCHA, then DOB, then LL84 (a DOB job more than 3 years after NYCHA's date wins:
    # the public-housing building was replaced)
    rank = allr.src.map({"nycha": 0, "dob": 1, "ll84": 2})
    w = allr[dec.str.startswith("write")].assign(rank=rank)
    dobyear = w[w.src == "dob"].set_index("bin").ry
    newer = w.bin.map(dobyear).fillna(-1)
    w.loc[(w.src == "nycha") & (newer > w.ry + 3), "rank"] = 9
    w = w.sort_values(["bin", "rank"]).drop_duplicates("bin")
    w = w[w.y.between(1800, TODAY)]

    note = (w.what + ". Assessor: " + np.where(w.p_raw > 0, w.p_raw.fillna(0).astype(int).astype(str), "none")
            + "; pipeline had " + w.p_src.fillna("none") + " " + w.p_year.round(1).astype(str)
            + " [" + w.decision.str.split(":").str[1] + "]")
    name = w.p_name.fillna(w.fp_name)
    if "rname" in w:
        name = name.fillna(w.rname)
    out = pd.DataFrame({"id": w.rid, "name": name.fillna(""), "lat": w.lat.round(6), "lon": w.lon.round(6),
                        "bin": w.bin, "start_year": w.y.round(2), "end_year": "", "source_url": w.source_url,
                        "note": note})
    assert not out.note[w.src != "ll84"].str.contains("estimate", case=False).any()
    out = out.sort_values(["bin"]).reset_index(drop=True)
    OUT_KNOWN.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_KNOWN, index=False)
    allr.drop(columns=["fp_name"]).to_parquet(WORK / "records_by_bin.parquet")
    rep["known_rows"] = int(len(out))
    rep["known_rows_by_source_decision"] = {f"{a}|{b}": int(v) for (a, b), v in
                                            w.groupby(["src", "decision"]).size().items()}
    rep["decisions_all_candidates"] = {f"{a}|{b}": int(v) for (a, b), v in
                                       allr.groupby(["src", "decision"]).size().items()}
    # quality table: record year minus the assessor's year where that is not a placeholder
    q = {}
    for k, g in allr[strong].groupby("kind"):
        dd = (g.ry - g.p_raw)
        q[k] = {"n": int(len(g)), "same_year": round(float((dd == 0).mean()), 3),
                "within_1": round(float((dd.abs() <= 1).mean()), 3), "within_2": round(float((dd.abs() <= 2).mean()), 3),
                "record_later_2plus": round(float((dd >= 2).mean()), 3),
                "record_earlier_2plus": round(float((dd <= -2).mean()), 3),
                "off_by_10plus": round(float((dd.abs() >= 10).mean()), 3),
                "median": float(dd.median()), "p10": float(dd.quantile(0.1)), "p90": float(dd.quantile(0.9))}
    rep["quality_record_minus_assessor_year"] = q
    hq = {}
    weak = allr.p_src.fillna("").str.startswith("heap")
    for k, g in allr[weak & (allr.kind != "ll84")].groupby("kind"):
        dd = g.ry - g.p_year
        hq[k] = {"n": int(len(g)), "within_3_of_pipeline_estimate": round(float((dd.abs() <= 3).mean()), 3),
                 "median": float(dd.median()), "p10": float(dd.quantile(0.1)), "p90": float(dd.quantile(0.9))}
    rep["quality_record_minus_pipeline_estimate_on_placeholder_years"] = hq
    log(f"records: {len(out)} rows -> {OUT_KNOWN.name} {rep['known_rows_by_source_decision']}")
    return out


# ------------------------------------------------------------------ demolished buildings
def _f(df):
    """DuckDB's nullable integers -> float64 with NaN (plain numpy semantics)."""
    import pandas as pd
    for col in df.columns:
        if pd.api.types.is_extension_array_dtype(df[col].dtype) and pd.api.types.is_numeric_dtype(df[col].dtype):
            df[col] = df[col].astype("float64")
    return df


def _round(o, nd=6):
    if isinstance(o, (list, tuple)):
        return [_round(x, nd) for x in o]
    return round(o, nd)


def demolished(c, heaps, rep):
    """demolished_footprints.geojson from OTI's BUILDING_HISTORIC layer (rules: building_records.md)."""
    import json
    import zlib

    import geopandas as gpd
    import numpy as np
    import pandas as pd
    import shapely

    from common import NYC_CRS

    h = c.execute(f"""select the_geom wkt, nullif(trim("NAME"), '') name, try_cast("BIN" as bigint) bin,
               try_cast("DOITT_ID" as bigint) doitt_id, "BASE_BBL" bbl, try_cast("CONSTRUCTION YEAR" as int) cy,
               try_cast("DEMOLITION YEAR" as int) dy, try_cast("FEATURE CODE" as int) fc, "GEOM SOURCE" gs,
               try_cast("HEIGHT ROOF" as double) hr, {D('"LAST_EDITED_DATE"')} led, "LAST_STATUS_TYPE" st,
               try_cast("OBJECTID" as int) oid
        from {csv('historic')}""").df()
    h = _f(h)
    rep["historic_rows"] = int(len(h))
    g = gpd.GeoDataFrame(h.drop(columns=["wkt"]), geometry=shapely.from_wkt(h.wkt.values), crs=4326).to_crs(NYC_CRS)
    del h
    geo = shapely.make_valid(g.geometry.values)
    bad = ~np.isin(shapely.get_type_id(geo), [3, 6])
    geo[bad] = shapely.buffer(geo[bad], 0)
    g["geometry"] = geo
    g["area"] = shapely.area(geo)
    g["boro"] = g.bbl.fillna("").str[:1]
    g.loc[~g.boro.isin(list("12345")), "boro"] = (g.bin.fillna(0) // 1000000).astype(int).astype(str)
    g["bin"] = g.bin.where(g.bin.fillna(0) % 1000000 != 0)
    g["edit"] = g.led.dt.year + (g.led.dt.day_of_year - 1) / 365.25
    g["is_dem"] = (g.st == "Demolition") | (g.dy.fillna(0) > 0)
    g["dy"] = g.dy.where(g.dy.between(1900, 2026))
    g["dyear"] = g.dy.fillna(np.floor(g.edit))  # the year used for comparisons
    g["name"] = g.name.where(~g.name.fillna("NO NAME").str.upper().isin(["NO NAME", "NONE", "N/A"]))

    # --- today's footprints on the same ground
    sy = c.execute("""select fp.bin, coalesce(year(n.done), nullif(p.p_raw, 0), nullif(fp.year_raw, 0)) s_year,
               p.p_year, p.p_src from fp left join pipe p using (bin)
               left join (select bin, done from nbbest where ok) n using (bin)""").df()
    sy = _f(sy).set_index("bin")
    pairs = []
    for b in "12345":
        f = c.execute(f"""select bin, geometry from '{INTERIM / "nyc_footprints_raw.parquet"}'
            where cast(floor(bin / 1000000) as int) = {b} or (bin is null and substr(base_bbl, 1, 1) = '{b}')""").df()
        fg = gpd.GeoSeries(shapely.from_wkb(f.geometry.map(bytes).values), crs=4326).to_crs(NYC_CRS)
        fgeo = shapely.make_valid(fg.values)
        del fg
        hb = g[g.boro == b]
        hi, si = shapely.STRtree(fgeo).query(hb.geometry.values, predicate="intersects")
        inter = shapely.area(shapely.intersection(hb.geometry.values[hi], fgeo[si]))
        fa = shapely.area(fgeo[si])
        pairs.append(pd.DataFrame({"h": hb.index.values[hi], "s_bin": f.bin.values[si], "inter": inter, "s_area": fa}))
        del f, fgeo
    pr = pd.concat(pairs, ignore_index=True)
    pr = pr[pr.inter > 0.5]
    pr["h_area"] = g["area"].reindex(pr.h).values
    pr["iou"] = pr.inter / (pr.h_area + pr.s_area - pr.inter)
    pr = pr.join(sy, on="s_bin")
    pr["older"] = pr.s_year < g.dyear.reindex(pr.h).values
    g["ov_any"] = (pr.groupby("h").inter.sum() / g["area"]).reindex(g.index).fillna(0).clip(0, 1)
    g["ov_older"] = (pr[pr.older].groupby("h").inter.sum() / g["area"]).reindex(g.index).fillna(0).clip(0, 1)
    best = pr.sort_values("iou").drop_duplicates("h", keep="last").set_index("h")
    g["best_iou"] = best.iou.reindex(g.index).fillna(0)
    g["best_older"] = best.older.reindex(g.index).fillna(False).astype(bool)
    big = pr.sort_values("inter").drop_duplicates("h", keep="last").set_index("h")
    g["standing_bin"] = big.s_bin.reindex(g.index)
    g["standing_year"] = big.s_year.reindex(g.index)

    # --- flags
    flag = pd.Series("", index=g.index)
    flag[~g.is_dem] = "superseded_outline"
    flag[(flag == "") & (g["area"] < 12)] = "tiny"
    flag[(flag == "") & ~g.dyear.between(1900, 2026)] = "no_valid_year"
    flag[(flag == "") & (g.best_iou > 0.6) & g.best_older] = "coincides_with_older_standing"
    flag[(flag == "") & (g.ov_older > 0.5)] = "inside_older_standing"

    # --- the same outline twice in the layer: keep the better record
    k = g[flag == ""]
    a, b_ = shapely.STRtree(k.geometry.values).query(k.geometry.values, predicate="intersects")
    m = a < b_
    a, b_ = a[m], b_[m]
    inter = shapely.area(shapely.intersection(k.geometry.values[a], k.geometry.values[b_]))
    iou = inter / (k["area"].values[a] + k["area"].values[b_] - inter)
    score = (k.dy.notna().astype(int) * 4 + (k.hr.fillna(0) > 0).astype(int) * 2 + (k.doitt_id.fillna(0) > 0).astype(int)
             ).values + k.edit.fillna(0).values / 1e4
    dup = set()
    for i, j in zip(a[iou > 0.6], b_[iou > 0.6]):
        if i in dup or j in dup:
            continue
        dup.add(j if score[i] >= score[j] else i)
    flag.loc[k.index[sorted(dup)]] = "duplicate_outline"
    g["flag"] = flag
    rep["historic_flagged"] = flag[flag != ""].value_counts().to_dict()

    # --- records by BIN / lot
    dm = c.execute(f"""select bin, {DEC.format('signoff')} so, year(signoff) so_y, year(first_permit) pm_y,
               {DEC.format('first_permit')} pm, est, eh from dm""").df()
    dm = _f(dm)
    nbj = c.execute(f"""select bin, {DEC.format('done')} y, year(done) ry, kind, job, ph, pst,
               (coalesce(pocc, '') in {GARAGE_OCC} and (coalesce(ph, 99) <= 15 or coalesce(pst, 9) <= 1)) small
        from nb""").df()
    nbj = _f(nbj)
    dof = c.execute(f"""select substr(bble, 1, 10) bbl, max(try_cast(yrb as int)) yrb, max(coalesce(yrb_flag, '')) yflag,
               max(try_cast(bldgs as int)) bldgs, max(try_cast(story as double)) story
        from (select bble, ease, yrb, yrb_flag, bldgs, story from {csv('dof_tc1_2010')}
              union all select bble, ease, yrb, yrb_flag, bldgs, story from {csv('dof_tc234_2010')})
        where coalesce(ease, '') = '' group by 1""").df()
    dof = _f(dof).set_index("bbl")

    w = g[flag == ""].copy()
    old_epoch = w.led.dt.year <= 2016
    gap = w.dyear - w.cy
    rep["historic_gap_old_epoch"] = {int(k_): int(v) for k_, v in gap[old_epoch & gap.between(-3, 12)].value_counts().sort_index().items()}
    rep["historic_gap_new_epoch"] = {int(k_): int(v) for k_, v in gap[~old_epoch & gap.between(-3, 12)].value_counts().sort_index().items()}
    # construction year on the record. Records edited before 2017 often carry the year of the building
    # that REPLACED the demolished one (the assessor's year of the lot, read after the demolition):
    # a year less than six years before the demolition is not used there.
    ok = w.cy.between(1800, 2026) & np.where(old_epoch, gap >= 6, gap >= 1)
    start = w.cy.where(ok).astype(float)
    ssrc = pd.Series(np.where(ok, "oti", ""), index=w.index)
    rep["historic_start_from_oti"] = int(ok.sum())
    rep["historic_construction_year_rejected"] = int((w.cy.between(1800, 2026) & ~ok).sum())
    # the assessment roll of fiscal 2010 for lots cleared from 2010 on (one building on the lot)
    d10 = dof.reindex(w.bbl.fillna("").values)
    y10 = pd.Series(d10.yrb.values, index=w.index, dtype="float")
    use10 = start.isna() & (w.dyear >= 2010) & (d10.bldgs.values == 1) & y10.between(1800, 2008) & (y10 <= w.dyear - 2)
    start[use10] = y10[use10]
    ssrc[use10] = "dof_roll_2010"
    rep["historic_start_from_roll_2010"] = int(use10.sum())
    flagged_e = pd.Series((d10.yflag.values == "E") & (d10.yrb.values == start.values), index=w.index)
    heap = pd.Series([(y_ in heaps.get(b, ())) if y_ == y_ else False for y_, b in zip(start, w.boro)], index=w.index)
    squal = pd.Series(np.where(start.isna(), None, np.where(heap | flagged_e, "estimated", "recorded")), index=w.index)
    # a completed DOB new-building job on the BIN, before the demolition
    j = nbj.merge(w[["bin", "dyear", "hr"]].assign(h=w.index).dropna(subset=["bin"]), on="bin")
    r = j.ph * 0.3048 / (j.hr * 0.3048)
    j = j[(j.ry <= j.dyear - 1) & ~j.small & (j.hr > 0) & r.between(0.55, 1.5)]
    j = j.sort_values("y").drop_duplicates("h", keep="last").set_index("h")
    use = j.index[(start.reindex(j.index).isna() | ((start.reindex(j.index) - j.ry).abs() <= 3)).values]
    start[use] = j.y.reindex(use).round(2)
    ssrc[use] = "dob_nb"
    squal[use] = "recorded"
    rep["historic_start_from_dob"] = int(len(use))

    # demolition: OTI's year; the day from a DOB demolition sign-off of the same year
    d = dm.merge(w[["bin", "dy", "edit"]].assign(h=w.index).dropna(subset=["bin"]), on="bin")
    both = d[d.dy.notna() & d.so_y.notna()]
    rep["oti_demolition_year_minus_dob_signoff_year"] = {int(k_): int(v) for k_, v in (both.dy - both.so_y).clip(-5, 5).value_counts().sort_index().items()}
    bp = d[d.dy.notna() & d.pm_y.notna()]
    rep["oti_demolition_year_minus_dob_permit_year"] = {int(k_): int(v) for k_, v in (bp.dy - bp.pm_y).clip(-5, 5).value_counts().sort_index().items()}
    # OTI's demolition year stands (82 % of the years that can be compared equal the year of the DOB
    # demolition sign-off). The day comes from the sign-off when it is the same year; a sign-off up to
    # three years BEFORE OTI's year wins (the building was certified gone by then). Rows without a
    # DOB demolition job are unconfirmed (end_check = none).
    end = (w.dy + 0.5).astype(float)
    esrc = pd.Series(np.where(w.dy.notna(), "oti_year", ""), index=w.index)
    equal = pd.Series(np.where(w.dy.notna(), "recorded", "estimated"), index=w.index)
    echeck = pd.Series("none", index=w.index)
    dd = d[d.dy.notna()]
    inwin = dd[(dd.pm_y <= dd.dy) | (dd.so_y >= dd.dy)]
    echeck[inwin.h.unique()] = "dob_job"
    same = dd[dd.so_y == dd.dy].sort_values("so").drop_duplicates("h", keep="last").set_index("h")
    end[same.index] = same.so.round(2)
    esrc[same.index] = "oti_year+dob_signoff"
    echeck[same.index] = "dob_signoff_same_year"
    early = dd[(dd.so_y < dd.dy) & (dd.so_y >= dd.dy - 3) & ~dd.h.isin(same.index)]
    early = early.sort_values("so").drop_duplicates("h", keep="last").set_index("h")
    end[early.index] = early.so.round(2)
    esrc[early.index] = "dob_signoff"
    echeck[early.index] = "dob_signoff_earlier"
    nody = w.index[w.dy.isna()]
    cand = d[d.h.isin(nody) & d.so.notna() & (d.so <= d.edit + 1)].sort_values("so").drop_duplicates("h", keep="last").set_index("h")
    end[cand.index] = cand.so.round(2)
    esrc[cand.index] = "dob_signoff"
    equal[cand.index] = "recorded"
    echeck[cand.index] = "dob_signoff"
    rest = nody.difference(cand.index)
    end[rest] = w.edit[rest].round(2)   # the day the outline was retired: demolished by then
    esrc[rest] = "oti_edit_date"
    retired = w.edit.where(w.edit >= np.floor(end)).round(2)
    late = (echeck == "none") & w.dy.notna() & (np.floor(w.edit) - w.dy >= 3)
    equal[late] = "estimated"   # the year on the record, but the outline stayed on the map 3+ years longer
    rep["historic_end_check"] = echeck.value_counts().to_dict()
    big_unconfirmed = w.index[(echeck == "none") & (w["area"] > 1000)]
    rep["historic_big_unconfirmed"] = int(len(big_unconfirmed))
    rep["historic_end_source"] = esrc.value_counts().to_dict()
    # storeys: the demolition job's "existing stories", else the 2010 roll
    st_ = d[(d.est > 0) & (d.est < 120)].sort_values("so").drop_duplicates("h", keep="last").set_index("h").est
    storeys = st_.reindex(w.index).astype(float)
    s10 = pd.Series(d10.story.values, index=w.index)
    f10 = storeys.isna() & (w.dyear >= 2010) & (d10.bldgs.values == 1) & (s10 > 0)
    storeys[f10] = s10[f10]
    height = (w.hr * 0.3048).where((w.hr > 0) & (w.hr < 2000)).round(1)

    # lifespans: no start >= end, years in range
    badspan = start.notna() & (start >= end - 0.01)
    start[badspan] = np.nan
    squal[badspan] = None
    ssrc[badspan] = ""
    keep = end.between(1800, TODAY + 0.5)
    assert keep.all(), "end year out of range"

    # --- ids
    cen = w.geometry.centroid
    ids = []
    seen = set()
    dcount = w.doitt_id.fillna(0).astype("int64").value_counts()
    for did, x, y_, e in zip(w.doitt_id.fillna(0).astype("int64"), cen.x, cen.y, end):
        if did > 0 and dcount[did] == 1:
            i_ = f"oti-h{did}"
        else:
            i_ = f"oti-hx{zlib.crc32(f'{x:.0f},{y_:.0f},{int(e)}'.encode()):08x}"
        while i_ in seen:
            i_ += "b"
        seen.add(i_)
        ids.append(i_)
    w["id"] = ids

    # --- write
    simp = shapely.simplify(w.geometry.values, 0.3, preserve_topology=True)
    ll = gpd.GeoSeries(simp, crs=NYC_CRS).to_crs(4326)
    feats = []
    note_rej = (w.cy.between(1800, 2026) & ~ok)
    for n_, (idx, row) in enumerate(w.iterrows()):
        gm = ll.iloc[n_]
        if gm.is_empty or gm.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        s_ = start[idx]
        notes = []
        if note_rej[idx] and ssrc[idx] != "oti":
            notes.append(f"construction year on the record ({int(row.cy)}) not used: not before the demolition, or the replacement's year")
        if late[idx]:
            notes.append("no DOB demolition job found and the outline was retired 3+ years after the year on the record: unconfirmed")
        if esrc[idx] == "oti_edit_date":
            notes.append("no demolition year on the record: end = the day the outline was retired (demolished by then)")
        props = {
            "id": row.id, "name": row["name"] if isinstance(row["name"], str) else None,
            "bin": int(row.bin) if row.bin == row.bin else None,
            "start_year": None if s_ != s_ else (int(s_) if float(s_).is_integer() else round(float(s_), 2)),
            "end_year": round(float(end[idx]), 2),
            "height_m": None if height[idx] != height[idx] else float(height[idx]),
            "storeys": None if storeys[idx] != storeys[idx] else float(storeys[idx]),
            "source": "oti_building_historic",
            "start_quality": squal[idx], "end_quality": equal[idx],
            "start_src": ssrc[idx] or None, "end_src": esrc[idx], "end_check": echeck[idx],
            "feature_code": int(row.fc) if row.fc == row.fc else None, "bbl": row.bbl if isinstance(row.bbl, str) else None,
            "retired": None if retired[idx] != retired[idx] else float(retired[idx]),
            "standing_bin": int(row.standing_bin) if row.standing_bin == row.standing_bin else None,
            "standing_overlap": round(float(row.ov_any), 2),
            "note": "; ".join(notes) or None,
        }
        mp = shapely.geometry.mapping(gm)
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": mp["type"], "coordinates": _round(mp["coordinates"])}})
    OUT_DEMO.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_DEMO, "w") as f:
        f.write('{"type":"FeatureCollection","name":"demolished_footprints","features":[\n')
        f.write(",\n".join(json.dumps(x, separators=(",", ":")) for x in feats))
        f.write("\n]}\n")
    rep["demolished_written"] = len(feats)
    rep["demolished_mb"] = round(OUT_DEMO.stat().st_size / 1e6, 1)
    rep["demolished_start_quality"] = squal.fillna("none").value_counts().to_dict()
    rep["demolished_end_quality"] = equal.value_counts().to_dict()
    rep["demolished_with_height"] = int(height.notna().sum())
    rep["demolished_with_storeys"] = int(storeys.notna().sum())
    rep["demolished_by_end_year"] = {int(k_): int(v) for k_, v in np.floor(end).value_counts().sort_index().items()}
    rep["demolished_no_standing_overlap"] = int((w.ov_any < 0.05).sum())
    lagy = (np.floor(w.edit) - np.floor(end))
    rep["demolished_unconfirmed_retired_3plus_years_after"] = int(((echeck == "none") & (lagy >= 3)).sum())
    wc = w.geometry.centroid.to_crs(4326)
    top = w.assign(end=end, lon=wc.x.round(5), lat=wc.y.round(5), area_m2=w["area"].round())[
        (echeck == "none") & (w["area"] > 4000)].sort_values("area_m2", ascending=False)
    top[["id", "bin", "bbl", "cy", "end", "edit", "area_m2", "lon", "lat"]].round(2).to_csv(
        WORK / "big_unconfirmed_demolitions.csv", index=False)

    # --- flagged rows (not written) and their outlines
    fl = g[g.flag != ""]
    cen = fl.geometry.centroid.to_crs(4326)
    pd.DataFrame({"objectid": fl.oid, "doitt_id": fl.doitt_id, "bin": fl.bin, "reason": fl.flag, "status": fl.st,
                  "construction_year": fl.cy, "demolition_year": fl.dy, "area_m2": fl["area"].round(1),
                  "best_iou": fl.best_iou.round(2), "share_under_older_standing": fl.ov_older.round(2),
                  "standing_bin": fl.standing_bin, "standing_year": fl.standing_year,
                  "lon": cen.x.round(6), "lat": cen.y.round(6)}).to_csv(OUT_FLAG, index=False)
    fl[["oid", "doitt_id", "bin", "flag", "st", "cy", "dy", "geometry"]].to_crs(4326).to_file(
        WORK / "flagged_outlines.geojson", driver="GeoJSON")

    # --- standing buildings that the pipeline starts before a demolition on their ground
    wp = pr[pr.h.isin(w.index)].copy()
    wp["h_end"] = end.reindex(wp.h).values
    wp["h_id"] = w.id.reindex(wp.h).values
    wp["share_of_standing"] = wp.inter / wp.s_area
    wp["share_of_demolished"] = wp.inter / wp.h_area
    cf = wp[((wp.share_of_standing >= 0.3) | (wp.share_of_demolished >= 0.5)) & (wp.p_year < wp.h_end)]
    cf = cf.sort_values("h_end").drop_duplicates("s_bin", keep="last")
    cf[["s_bin", "h_end", "h_id", "share_of_standing", "share_of_demolished", "p_year", "p_src", "s_year"]].rename(
        columns={"s_bin": "bin", "h_end": "not_before"}).round(3).to_csv(WORK / "standing_after_demolition.csv", index=False)
    rep["standing_started_before_a_demolition_on_their_ground"] = int(len(cf))
    rep["standing_started_before_by_src"] = cf.p_src.value_counts().to_dict()
    log(f"records: {len(feats)} demolished footprints -> {OUT_DEMO.name} ({rep['demolished_mb']} MB); "
        f"flagged {rep['historic_flagged']}")


def demolitions_without_outline(c, rep):
    """DOB demolition jobs against OTI's historic layer: how complete the layer is, and the signed-off
    demolitions whose BIN is in neither layer (a building certainly gone, no outline in the city's data)."""
    c.execute(f"""create table hbin as select distinct try_cast("BIN" as bigint) bin from {csv('historic')}
                  where try_cast("BIN" as bigint) is not null""")
    c.execute("""create table dmb as
        select bin, max(signoff) signoff, min(first_permit) first_permit, max(est) storeys, max(eh) height_ft,
               any_value(boro) boro, any_value(block) block, any_value(lot) lot, any_value(house) house,
               any_value(street) street, max(lat) lat, max(lon) lon, any_value(job) job
        from dm where signoff is not null group by 1""")
    cov = c.execute("""select cast(floor(year(signoff) / 5) * 5 as int) period, count(*) bins,
               round(avg((bin in (select bin from hbin))::int), 3) in_historic_layer,
               round(avg((bin in (select bin from fp))::int), 3) bin_in_todays_footprints,
               round(avg((bin not in (select bin from hbin) and bin not in (select bin from fp))::int), 3) in_neither
        from dmb group by 1 order by 1""").df()
    rep["dob_demolitions_vs_historic_layer"] = cov.to_dict("records")
    t = c.execute(f"""select job, bin, boro, block, lot, house, street, strftime(signoff, '%Y-%m-%d') signoff,
               round({DEC.format('signoff')}, 2) end_year, strftime(first_permit, '%Y-%m-%d') first_permit,
               storeys, height_ft, lat, lon
        from dmb where bin not in (select bin from hbin) and bin not in (select bin from fp) order by signoff""").df()
    t.to_csv(WORK / "dob_demolitions_without_outline.csv", index=False)
    rep["dob_demolitions_without_outline"] = int(len(t))
    # footprints OTI marks for demolition whose DOB demolition job is signed off: gone, not yet retired
    m = c.execute(f"""select f.bin, f.status, strftime(d.signoff, '%Y-%m-%d') signoff, round({DEC.format('d.signoff')}, 2) end_year,
               f.lon, f.lat, f.height_m, f.year_raw
        from (select bin, any_value(status) status, any_value(lon) lon, any_value(lat) lat, max(height_m) height_m,
                     max(year_raw) year_raw from '{INTERIM / "nyc_footprints_raw.parquet"}'
              where status in ('Marked for Demolition', 'Investigate Demolition', 'Demolition') group by 1) f
        join dmb d using (bin)""").df()
    m.to_csv(WORK / "standing_marked_for_demolition.csv", index=False)
    rep["standing_marked_for_demolition_with_signed_off_job"] = int(len(m))


# legal class of a multiple dwelling -> (not before, not after). Multiple Dwelling Law s. 4: an old-law
# tenement existed before 12 April 1901; a new-law tenement was erected between then and 18 April 1929;
# "heretofore" erected or converted = before 18 April 1929. The "hereafter erected", "converted ... law"
# and single-room-occupancy classes are left out: where the Landmarks Commission has an exact date they
# fail it too often (31-68 %; buildings reclassified after an alteration).
HPD_CLASS = {
    "OLD LAW TENEMENT": (None, 1901.28),
    "NEW LAW TENEMENT": (1901.28, 1929.3),
    "HERETOFORE ERECTED EXISTING CLASS A": (None, 1929.3), "HERETOFORE ERECTED EXISTING CLASS B": (None, 1929.3),
    "HERETOFORE CONVERTED CLASS A": (None, 1929.3), "HERETOFORE CONVERTED CLASS B": (None, 1929.3),
}
MDL_URL = "https://www.nysenate.gov/legislation/laws/MDW/4"


def bounds(c, rep):
    """data/interim/records/year_bounds.csv: bounds on the construction year from HPD's legal class of
    multiple dwellings; dof_flagged_estimates.csv: years the assessor itself flags as estimated."""
    import numpy as np
    import pandas as pd
    h = _f(c.execute(f"""select try_cast(bin as bigint) bin, regexp_replace(upper(trim(dobbuildingclass)), ' +', ' ', 'g') cls,
               count(*) n from {csv('hpd_buildings')}
        where lifecycle = 'Building' and recordstatus = 'Active' and dobbuildingclass is not null group by 1, 2""").df())
    h = h[h.cls.isin(list(HPD_CLASS)) & h.bin.notna() & (h.bin % 1000000 != 0)]
    h = h[~h.bin.duplicated(keep=False)]  # one class per BIN
    h["not_before"] = h.cls.map(lambda k: HPD_CLASS[k][0])
    h["not_after"] = h.cls.map(lambda k: HPD_CLASS[k][1])
    p = _f(c.execute("select bin, p_year, p_src, p_conf, p_raw from pipe").df())
    h = h.merge(p, on="bin", how="inner")
    h["violates"] = (h.p_year < h.not_before.fillna(-1e9) - 1) | (h.p_year > h.not_after.fillna(1e9) + 1)
    h["source_url"] = url("hpd_buildings")
    h[["bin", "not_before", "not_after", "cls", "p_year", "p_src", "p_conf", "violates", "source_url"]].round(2).to_csv(
        WORK / "year_bounds.csv", index=False)
    exact = h.p_conf == "exact"
    out3 = (h.p_year < h.not_before.fillna(-1e9) - 3) | (h.p_year > h.not_after.fillna(1e9) + 3)
    lp = exact & (h.p_src == "lpc")
    rep["hpd_class_checked_against_lpc_exact_dates"] = {
        k: [int(len(g_)), round(float(1 - out3[g_.index].mean()), 3)] for k, g_ in h[lp].groupby("cls")}
    rep["hpd_class_assessor_exact_years_outside_by_3plus"] = {
        k: [int(len(g_)), int(out3[g_.index].sum())] for k, g_ in h[exact & (h.p_src == "assessor")].groupby("cls")}
    rep["hpd_class_bounds"] = {
        "bins": int(len(h)),
        "by_class": h.cls.value_counts().to_dict(),
        "pipeline_exact_years_inside_bounds": {k: [int(len(g_)), round(float((~g_.violates).mean()), 3)]
                                               for k, g_ in h[exact].groupby("p_src")},
        "pipeline_estimates_outside_bounds": {k: [int(len(g_)), int(g_.violates.sum())]
                                              for k, g_ in h[~exact].groupby("p_src")},
        "outside_by_class": h[~exact & h.violates].cls.value_counts().to_dict(),
    }
    d = _f(c.execute(f"""select fp.bin, d.yrb, p.p_year, p.p_src from fp join pipe p using (bin)
        join (select substr(bble, 1, 10) bbl, max(try_cast(yrb as int)) yrb, max(coalesce(yrb_flag, '')) flag
              from (select bble, ease, yrb, yrb_flag from {csv('dof_tc1_2017')}
                    union all select bble, ease, yrb, yrb_flag from {csv('dof_tc234_2017')})
              where coalesce(ease, '') = '' group by 1) d on d.bbl = fp.bbl
        where d.flag = 'E' and p.p_src = 'assessor' and p.p_conf = 'exact' and d.yrb = p.p_raw""").df())
    d.to_csv(WORK / "dof_flagged_estimates.csv", index=False)
    rep["dof_flagged_estimates_treated_as_exact"] = int(len(d))
    log(f"records: {len(h)} BINs with a legal-class bound ({int(h.violates.sum())} pipeline years outside), "
        f"{len(d)} assessor years flagged as estimates by Finance but exact in the pipeline")


def main():
    import json
    WORK.mkdir(parents=True, exist_ok=True)
    rep = {}
    c = db()
    load_today(c)
    heaps = heap_sets(c)
    rep["placeholder_years"] = {b: sorted(int(x) for x in v) for b, v in heaps.items()}
    rep.update(norm_dob(c))
    rep.update(dob_candidates(c))
    standing_records(c, rep)
    demolished(c, heaps, rep)
    demolitions_without_outline(c, rep)
    bounds(c, rep)
    (WORK / "report.json").write_text(json.dumps(rep, indent=1, default=str))
    return rep


if __name__ == "__main__":
    download()
    if "download" not in sys.argv[1:]:
        main()
