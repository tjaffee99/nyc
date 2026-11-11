/**
 * Trenton and New Brunswick, New Jersey: landmarks added in the towns round (2026-11-11, second pass).
 * Research, sources, ids of the footprints and numeric checks: data/research/towns_nj.md.
 *
 * Conventions as princeton.ts: the anchor is a point inside the footprint; plans are the real outlines
 * of data/interim/counties/nj_mercer.parquet (Trenton) and nj_middlesex.parquet (New Brunswick)
 * (Overture / OpenStreetMap, ODbL) re-expressed in anchor-local metres (x east, y north). Heights are
 * cited figures where the note gives one; otherwise estimates, named in each model's `Model:` fact.
 */
import {MeshBuilder, circle, lngLatToLocal, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OVERTURE = 'https://docs.overturemaps.org/guides/buildings/';

export const NJ_TOWNS: Landmark[] = [];

