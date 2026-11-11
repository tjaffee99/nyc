/**
 * New York landmarks, round "more A": the High Line (viaduct of 1934 and the park), the
 * James A. Farley Building / Moynihan Train Hall, the Brooklyn Tower with the Dime Savings
 * Bank. Research and numeric checks: data/research/landmarks_more_a.md.
 *
 * Conventions as in nyc-civic.ts: anchor = a point on the structure, plans from
 * OpenStreetMap ways (ODbL, way ids in the facts) and the city's footprints, heights cited
 * or named as estimates in the `Model:` fact. Models that change are additive where the
 * old part stays (the annex, the bank's enlargement) so that nothing sinks and reappears.
 */
import {MeshBuilder, rect, rotRect, type V2} from './kit';
import type {Landmark} from './types';

const WIKI = 'https://en.wikipedia.org/wiki/';
const OSM = 'https://www.openstreetmap.org/';
const FOOTPRINTS = 'https://data.cityofnewyork.us/d/5zhs-2jue';

export const MORE_A: Landmark[] = [];

const HL: Record<string, any> = {"S1":{"anchor":[-74.007366,40.742815],"ring":[[91.3,314.8],[83.3,298.3],[76.4,279.2],[76.9,278.9],[62.5,254.1],[49.0,229.2],[42.2,214.5],[39.2,204.8],[37.3,195.3],[36.1,185.9],[35.8,173.2],[38.0,172.7],[36.7,161.1],[38.8,131.1],[50.5,124.1],[43.5,111.5],[45.4,101.4],[50.7,99.0],[44.8,89.2],[44.0,66.9],[36.7,47.5],[32.1,50.0],[-15.8,-35.7],[-21.4,-51.0],[-25.9,-75.3],[-29.4,-114.5],[-52.6,-251.4],[-57.0,-263.3],[-61.3,-282.4],[-64.6,-328.1],[-66.9,-373.4],[-80.7,-373.2],[-74.4,-271.7],[-66.6,-234.7],[-50.9,-137.6],[-45.5,-108.3],[-36.6,-42.8],[-8.5,7.7],[-13.0,10.3],[-6.1,22.7],[-2.0,19.8],[19.6,57.3],[13.9,60.2],[21.7,73.5],[12.7,97.3],[9.7,100.6],[12.2,105.3],[27.1,83.0],[30.3,73.2],[31.8,83.0],[32.0,109.7],[23.2,114.5],[31.0,128.6],[25.2,167.3],[21.3,169.5],[27.0,179.0],[22.3,181.5],[27.4,190.6],[23.1,192.6],[28.0,201.6],[26.6,202.4],[30.9,210.3],[29.9,210.9],[34.1,218.5],[33.3,219.0],[43.2,236.5],[42.8,236.9],[68.2,283.7],[76.6,306.8],[105.5,359.1],[113.4,354.7]],"par":[[[91.3,314.8],[83.3,298.3],[76.4,279.2],[76.9,278.9],[62.5,254.1],[49.0,229.2],[42.2,214.5],[39.2,204.8],[37.3,195.3],[36.1,185.9],[35.8,173.2],[38.0,172.7],[36.7,161.1],[38.8,131.1],[50.5,124.1],[43.5,111.5],[45.4,101.4],[50.7,99.0],[44.8,89.2],[44.0,66.9],[36.7,47.5],[32.1,50.0],[-15.8,-35.7],[-21.4,-51.0],[-25.9,-75.3],[-29.4,-114.5],[-52.6,-251.4],[-57.0,-263.3],[-61.3,-282.4],[-64.6,-328.1],[-66.9,-373.4],[-80.7,-373.2],[-74.4,-271.7],[-66.6,-234.7],[-50.9,-137.6],[-45.5,-108.3],[-36.6,-42.8],[-8.5,7.7],[-13.0,10.3],[-6.1,22.7],[-2.0,19.8],[19.6,57.3],[13.9,60.2],[21.7,73.5],[12.7,97.3],[9.7,100.6],[12.2,105.3],[27.1,83.0],[30.3,73.2],[31.8,83.0],[32.0,109.7],[23.2,114.5],[31.0,128.6],[25.2,167.3],[21.3,169.5],[27.0,179.0],[22.3,181.5],[27.4,190.6],[23.1,192.6],[28.0,201.6],[26.6,202.4],[30.9,210.3],[29.9,210.9],[34.1,218.5],[33.3,219.0],[43.2,236.5],[42.8,236.9],[68.2,283.7],[76.6,306.8],[105.5,359.1]],[[113.4,354.7],[91.3,314.8]]],"spine":[[-69.2,-373.6],[-70.3,-361.1],[-75.7,-341.7],[-75.8,-332.4],[-66.3,-281.6],[-63.1,-246.4],[-60.4,-230.7],[-50.1,-188.1],[-45.3,-160.5],[-34.9,-122.9],[-31.4,-99.2],[-29.3,-66.6],[-27.6,-58.8],[-23.1,-43.5],[-18.2,-32.6],[32.8,57.7],[39.2,75.1],[39.6,94.5],[33.4,133.3],[33.8,160.7],[32.2,187.8],[33.4,199.0],[49.9,242.7],[72.7,279.8],[85.4,316.8],[107.7,357.8]],"bents":[[-73.5,-368.0,-0.997,-0.076,6.9],[-72.9,-356.5,-0.95,-0.312,7.3],[-72.2,-344.2,-0.981,-0.196,6.9],[-71.6,-333.5,-0.992,0.127,6.7],[-70.8,-321.7,-0.988,0.154,6.7],[-70.0,-309.9,-0.988,0.157,6.7],[-69.2,-298.0,-0.981,0.192,6.8],[-68.4,-286.0,-0.97,0.243,6.9],[-67.1,-274.4,-0.997,0.081,7.4],[-64.7,-262.7,-0.996,0.087,7.7],[-61.3,-251.1,-0.997,0.083,8.6],[-59.1,-239.7,-0.984,0.178,8.4],[-57.1,-228.0,-0.98,0.198,8.3],[-55.1,-216.4,-0.967,0.254,8.4],[-53.2,-204.7,-0.968,0.251,8.5],[-51.2,-192.9,-0.973,0.229,8.5],[-49.3,-181.2,-0.986,0.167,8.5],[-47.4,-169.5,-0.987,0.163,8.6],[-45.4,-157.7,-0.969,0.246,8.6],[-43.4,-145.9,-0.959,0.282,8.7],[-41.4,-134.1,-0.96,0.281,8.7],[-39.4,-122.8,-0.983,0.183,8.6],[-37.5,-111.3,-0.989,0.147,8.4],[-36.1,-99.6,-0.992,0.124,8.1],[-34.9,-88.1,-0.998,0.06,7.8],[-33.5,-76.2,-0.997,0.074,7.5],[-31.7,-64.0,-0.977,0.211,7.8],[-29.8,-52.1,-0.965,0.263,8.1],[-26.1,-40.4,-0.928,0.373,8.1],[-20.7,-29.4,-0.887,0.462,7.4],[-14.8,-18.9,-0.87,0.494,7.4],[-9.1,-8.5,-0.871,0.492,7.4],[-3.3,1.8,-0.872,0.49,7.4],[0.2,13.5,-0.873,0.488,10.0],[8.2,22.6,-0.873,0.488,7.5],[14.1,32.9,-0.873,0.488,7.4],[19.9,43.2,-0.876,0.482,7.3],[23.3,55.5,-0.839,0.544,10.4],[30.1,64.2,-0.914,0.406,12.0],[37.4,73.6,-0.972,0.233,7.0],[38.2,85.0,-1.0,-0.004,6.4],[41.1,97.1,-0.991,-0.131,9.3],[37.9,108.7,-0.981,-0.194,6.0],[37.6,120.7,-0.982,-0.189,12.5],[34.6,132.0,-0.999,-0.052,4.1],[33.3,143.9,-1.0,0.03,4.6],[32.0,155.7,-1.0,0.004,5.1],[31.3,167.4,-0.996,-0.086,6.1],[31.5,179.3,-0.997,-0.074,4.5],[30.9,191.4,-0.999,0.053,5.8],[33.2,203.3,-0.958,0.285,5.6],[37.3,214.5,-0.933,0.359,4.7],[42.2,225.4,-0.925,0.38,4.6],[47.5,236.0,-0.925,0.38,4.6],[53.1,246.4,-0.862,0.506,4.5],[58.8,256.8,-0.838,0.546,4.5],[64.6,267.2,-0.834,0.551,4.7],[70.4,277.4,-0.885,0.465,4.9],[74.8,288.3,-0.948,0.32,4.6],[78.8,299.4,-0.958,0.287,4.6],[83.9,310.2,-0.945,0.326,4.7],[89.4,320.6,-0.885,0.465,4.5],[95.1,330.9,-0.875,0.484,4.5],[100.8,341.3,-0.875,0.484,4.5],[106.6,351.7,-0.875,0.485,4.5]]},"S2":{"anchor":[-74.003716,40.749245],"ring":[[137.2,369.5],[148.5,346.0],[146.4,346.3],[149.2,336.9],[150.9,337.3],[152.1,332.7],[154.2,317.1],[154.7,301.9],[152.7,288.3],[154.8,286.9],[149.8,277.6],[150.4,277.4],[143.5,259.5],[77.0,138.8],[42.8,75.1],[42.1,67.8],[-75.0,-140.8],[-194.4,-356.4],[-202.3,-352.0],[-133.4,-227.2],[-136.3,-225.7],[-84.8,-129.0],[-80.0,-131.3],[-13.3,-10.6],[-6.4,6.2],[130.8,254.3],[141.9,284.1],[143.9,293.1],[145.4,307.6],[144.3,322.9],[140.0,340.1],[134.6,353.5],[127.2,364.8]],"par":[[[137.2,369.5],[148.5,346.0],[146.4,346.3],[149.2,336.9],[150.9,337.3],[152.1,332.7],[154.2,317.1],[154.7,301.9],[152.7,288.3],[154.8,286.9],[149.8,277.6],[150.4,277.4],[143.5,259.5],[77.0,138.8],[42.8,75.1],[42.1,67.8],[-75.0,-140.8],[-194.4,-356.4]],[[-202.3,-352.0],[-133.4,-227.2],[-136.3,-225.7],[-84.8,-129.0],[-80.0,-131.3],[-13.3,-10.6],[-6.4,6.2],[130.8,254.3],[141.9,284.1],[143.9,293.1],[145.4,307.6],[144.3,322.9],[140.0,340.1],[134.6,353.5],[127.2,364.8]]],"spine":[[-200.1,-353.2],[-166.4,-292.7],[-142.0,-256.4],[-124.7,-221.1],[-109.7,-197.9],[-59.1,-107.4],[-43.4,-71.2],[-23.1,-42.1],[-3.6,-7.2],[16.3,40.5],[139.8,264.9],[145.4,279.8],[148.2,291.4],[149.5,315.2],[144.7,338.5],[132.3,367.2]],"bents":[[-195.5,-349.0,-0.874,0.486,4.5],[-189.8,-338.7,-0.874,0.486,4.5],[-184.1,-328.4,-0.874,0.486,4.5],[-178.4,-318.1,-0.874,0.486,4.5],[-172.7,-307.8,-0.874,0.486,4.5],[-167.0,-297.5,-0.873,0.488,4.5],[-161.3,-287.2,-0.838,0.546,4.6],[-155.6,-276.9,-0.818,0.576,4.6],[-149.9,-266.5,-0.818,0.575,4.6],[-144.2,-256.3,-0.855,0.519,4.6],[-138.6,-246.2,-0.912,0.41,4.6],[-132.9,-235.8,-0.913,0.408,4.6],[-128.6,-224.7,-0.877,0.48,6.3],[-122.9,-214.1,-0.833,0.553,6.4],[-117.3,-203.7,-0.833,0.554,6.5],[-111.8,-193.6,-0.874,0.487,6.6],[-106.2,-183.3,-0.873,0.487,6.7],[-100.5,-172.9,-0.873,0.487,6.8],[-94.9,-162.5,-0.873,0.487,6.9],[-89.3,-152.3,-0.884,0.468,7.0],[-83.7,-141.9,-0.89,0.455,7.1],[-75.7,-132.8,-0.871,0.491,4.5],[-69.9,-122.5,-0.861,0.509,4.6],[-64.2,-112.1,-0.853,0.522,4.6],[-58.5,-102.0,-0.902,0.433,4.6],[-52.8,-91.7,-0.929,0.37,4.7],[-47.0,-81.4,-0.93,0.369,4.7],[-41.4,-71.2,-0.86,0.51,4.7],[-35.7,-61.0,-0.807,0.59,4.8],[-29.9,-50.6,-0.807,0.591,4.8],[-24.2,-40.4,-0.859,0.511,4.8],[-18.5,-30.2,-0.874,0.485,4.9],[-12.8,-19.9,-0.874,0.486,4.9],[-7.2,-9.5,-0.875,0.485,5.2],[-2.2,1.0,-0.908,0.419,5.9],[3.4,11.3,-0.939,0.345,6.2],[9.2,21.7,-0.942,0.336,6.2],[14.9,32.0,-0.916,0.401,6.2],[20.6,42.1,-0.882,0.472,6.2],[26.3,52.4,-0.876,0.481,6.2],[32.0,62.7,-0.877,0.481,6.3],[37.3,73.3,-0.877,0.481,5.8],[42.1,84.1,-0.877,0.481,4.8],[47.8,94.4,-0.877,0.481,4.7],[53.4,104.8,-0.877,0.481,4.7],[59.1,115.1,-0.877,0.481,4.6],[64.7,125.5,-0.877,0.48,4.5],[70.4,135.8,-0.877,0.48,4.5],[76.0,146.2,-0.877,0.48,4.4],[81.7,156.5,-0.874,0.486,4.4],[87.4,166.8,-0.871,0.491,4.4],[93.1,177.1,-0.868,0.497,4.4],[98.8,187.4,-0.869,0.494,4.4],[104.5,197.8,-0.872,0.49,4.4],[110.2,208.1,-0.874,0.487,4.3],[115.9,218.4,-0.874,0.486,4.3],[121.6,228.7,-0.874,0.486,4.3],[127.3,239.0,-0.874,0.486,4.3],[133.0,249.4,-0.88,0.474,4.3],[138.2,260.0,-0.897,0.443,4.9],[142.5,271.0,-0.928,0.373,5.1],[146.6,282.1,-0.962,0.272,5.1],[148.7,293.7,-0.988,0.153,4.7],[149.9,305.5,-0.999,0.033,4.7],[149.4,317.3,-0.996,-0.092,4.7],[147.7,329.0,-0.975,-0.223,4.8],[144.1,340.2,-0.942,-0.336,4.0],[140.5,351.5,-0.916,-0.402,4.8],[135.1,362.0,-0.905,-0.426,5.1]]},"S3":{"anchor":[-74.005559,40.754206],"ring":[[166.8,-98.3],[139.6,-83.2],[139.9,-82.7],[124.7,-74.3],[124.4,-74.8],[113.6,-68.9],[113.9,-68.3],[95.9,-58.5],[95.7,-59.0],[90.7,-56.2],[91.0,-55.8],[79.1,-49.2],[79.3,-48.9],[-12.8,0.9],[-9.6,6.8],[-16.3,15.0],[-22.8,25.5],[-28.0,36.2],[-32.7,51.3],[-34.7,66.6],[-35.0,75.7],[-32.7,96.3],[-28.1,110.1],[-22.2,123.7],[29.2,215.9],[47.5,231.2],[56.5,236.9],[70.0,243.4],[81.9,247.2],[93.8,249.5],[105.5,250.4],[118.2,249.5],[128.3,247.7],[127.2,241.4],[117.7,243.2],[110.8,243.8],[96.5,243.4],[82.5,240.9],[70.7,237.0],[64.0,234.0],[53.9,227.6],[36.9,212.6],[37.3,212.1],[-14.9,116.6],[-20.0,103.7],[-21.9,97.5],[-23.4,91.4],[-24.9,69.1],[-24.5,64.2],[-23.8,59.1],[-20.8,46.4],[-19.0,41.1],[-12.7,27.8],[-2.4,13.3],[2.4,8.3],[11.9,0.0],[25.3,-8.6],[95.2,-48.1],[100.3,-50.6],[100.1,-51.0],[118.0,-60.9],[118.1,-60.6],[129.0,-66.6],[128.8,-66.9],[144.1,-75.3],[144.3,-74.9],[171.5,-90.0],[171.3,-90.4],[186.1,-98.6],[186.3,-98.2],[197.1,-104.1],[196.9,-104.5],[243.3,-130.2],[243.6,-129.7],[314.4,-168.8],[304.0,-173.7],[295.8,-169.1],[293.5,-173.4],[289.1,-171.0],[292.6,-179.0],[282.6,-183.7],[265.9,-158.4],[236.6,-142.3],[239.2,-137.7],[215.4,-124.5],[215.2,-124.9],[210.3,-122.2],[210.5,-121.8],[192.6,-111.9],[192.3,-112.3],[181.6,-106.3],[181.9,-105.9],[167.1,-97.8]],"par":[[[166.8,-98.3],[139.6,-83.2],[139.9,-82.7],[124.7,-74.3],[124.4,-74.8],[113.6,-68.9],[113.9,-68.3],[95.9,-58.5],[95.7,-59.0],[90.7,-56.2],[91.0,-55.8],[79.1,-49.2],[79.3,-48.9],[-12.8,0.9],[-9.6,6.8],[-16.3,15.0],[-22.8,25.5],[-28.0,36.2],[-32.7,51.3],[-34.7,66.6],[-35.0,75.7],[-32.7,96.3],[-28.1,110.1],[-22.2,123.7],[29.2,215.9],[47.5,231.2],[56.5,236.9],[70.0,243.4],[81.9,247.2],[93.8,249.5],[105.5,250.4],[118.2,249.5],[128.3,247.7]],[[127.2,241.4],[117.7,243.2],[110.8,243.8],[96.5,243.4],[82.5,240.9],[70.7,237.0],[64.0,234.0],[53.9,227.6],[36.9,212.6],[37.3,212.1],[-14.9,116.6],[-20.0,103.7],[-21.9,97.5],[-23.4,91.4],[-24.9,69.1],[-24.5,64.2],[-23.8,59.1],[-20.8,46.4],[-19.0,41.1],[-12.7,27.8],[-2.4,13.3],[2.4,8.3],[11.9,0.0],[25.3,-8.6],[95.2,-48.1],[100.3,-50.6],[100.1,-51.0],[118.0,-60.9],[118.1,-60.6],[129.0,-66.6],[128.8,-66.9],[144.1,-75.3],[144.3,-74.9],[171.5,-90.0],[171.3,-90.4],[186.1,-98.6],[186.3,-98.2],[197.1,-104.1],[196.9,-104.5],[243.3,-130.2],[243.6,-129.7],[314.4,-168.8]],[[304.0,-173.7],[295.8,-169.1],[293.5,-173.4],[289.1,-171.0],[292.6,-179.0]],[[282.6,-183.7],[265.9,-158.4],[236.6,-142.3],[239.2,-137.7],[215.4,-124.5],[215.2,-124.9],[210.3,-122.2],[210.5,-121.8],[192.6,-111.9],[192.3,-112.3],[181.6,-106.3],[181.9,-105.9],[167.1,-97.8],[166.8,-98.3]]],"spine":[[287.7,-181.3],[280.3,-166.5],[270.5,-154.4],[232.1,-127.0],[195.8,-111.5],[148.1,-82.3],[112.1,-65.4],[11.1,-8.8],[-1.3,1.2],[-11.9,13.1],[-20.4,26.5],[-26.9,41.0],[-31.1,56.4],[-32.5,72.2],[-31.5,88.1],[-27.9,103.6],[-22.0,118.4],[-12.9,136.2],[18.1,192.2],[28.8,209.0],[39.3,221.0],[48.5,228.6],[62.0,237.0],[73.0,241.7],[88.3,245.8],[100.2,247.3],[116.1,247.2],[128.0,245.7]],"bents":[[284.8,-176.1,-0.902,-0.432,6.0],[283.1,-163.2,-0.843,-0.537,11.7],[273.3,-155.1,-0.707,-0.707,8.2],[263.1,-148.7,-0.551,-0.834,7.2],[252.6,-142.9,-0.578,-0.816,7.2],[242.1,-137.1,-0.595,-0.804,7.2],[233.1,-129.4,-0.547,-0.837,4.3],[222.9,-123.8,-0.37,-0.929,4.3],[212.4,-118.2,-0.347,-0.938,4.6],[202.1,-112.2,-0.416,-0.909,4.3],[191.9,-106.6,-0.53,-0.848,4.8],[181.5,-100.9,-0.549,-0.836,4.2],[171.1,-95.1,-0.535,-0.845,4.3],[160.7,-89.4,-0.499,-0.867,4.8],[150.3,-83.7,-0.489,-0.872,4.8],[139.9,-77.8,-0.42,-0.908,4.3],[129.4,-72.1,-0.407,-0.913,4.2],[119.0,-66.5,-0.421,-0.907,4.7],[108.8,-60.7,-0.511,-0.859,4.2],[98.4,-55.0,-0.498,-0.867,4.3],[88.0,-49.1,-0.478,-0.878,4.4],[77.6,-43.1,-0.454,-0.891,4.3],[67.3,-37.4,-0.476,-0.879,4.4],[56.9,-31.7,-0.48,-0.877,4.5],[46.5,-25.9,-0.48,-0.877,4.6],[36.1,-20.2,-0.483,-0.876,4.7],[25.8,-14.5,-0.502,-0.865,4.8],[15.6,-8.6,-0.545,-0.838,5.2],[5.7,-2.4,-0.628,-0.778,6.0],[-4.1,4.3,-0.718,-0.696,7.5],[-9.7,14.9,-0.802,-0.597,5.0],[-16.3,24.4,-0.863,-0.504,4.9],[-21.6,34.7,-0.913,-0.409,5.1],[-25.7,45.5,-0.954,-0.3,5.0],[-28.4,56.8,-0.984,-0.18,5.0],[-29.8,68.2,-0.999,-0.051,5.0],[-29.4,79.8,-0.998,0.065,5.2],[-28.3,91.3,-0.983,0.182,4.9],[-25.5,102.5,-0.955,0.297,4.9],[-21.4,113.3,-0.918,0.396,4.9],[-16.4,124.0,-0.893,0.45,4.9],[-10.7,134.3,-0.882,0.471,4.9],[-5.0,144.7,-0.878,0.478,4.8],[0.7,155.1,-0.875,0.484,4.7],[6.5,165.5,-0.873,0.489,4.7],[12.2,175.9,-0.873,0.489,4.6],[18.0,186.3,-0.872,0.489,4.6],[23.7,196.6,-0.859,0.513,4.5],[29.3,206.9,-0.811,0.584,4.5],[35.9,216.7,-0.736,0.677,3.7],[44.9,224.4,-0.641,0.767,3.6],[54.1,231.6,-0.543,0.84,3.2],[64.4,237.4,-0.435,0.901,3.0],[75.3,241.8,-0.315,0.949,3.1],[86.7,244.9,-0.201,0.979,3.2],[98.4,246.6,-0.081,0.997,3.2],[110.2,246.9,0.034,0.999,3.1],[122.0,245.6,0.136,0.991,3.2]]},"SB":{"anchor":[-74.0082,40.737815],"ring":[[17.5,177.8],[13.7,116.5],[13.2,110.7],[11.0,99.1],[-0.9,-82.3],[-6.6,-178.6],[-15.8,-178.2],[-10.1,-81.7],[1.9,100.4],[4.1,111.9],[4.5,117.1],[8.3,178.6]],"par":[[[17.5,177.8],[13.7,116.5],[13.2,110.7],[11.0,99.1],[-0.9,-82.3],[-6.6,-178.6],[-15.8,-178.2],[-10.1,-81.7],[1.9,100.4],[4.1,111.9],[4.5,117.1],[8.3,178.6],[17.5,177.8]]],"spine":[[12.9,178.2],[9.1,116.8],[6.4,99.8],[-11.2,-178.4]],"bents":[[12.6,172.5,0.998,-0.061,4.6],[11.8,161.0,0.998,-0.062,4.6],[11.1,149.4,0.998,-0.062,4.6],[10.4,137.9,0.998,-0.061,4.6],[9.7,126.4,0.998,-0.059,4.6],[8.9,114.9,0.996,-0.087,4.6],[7.2,103.5,0.979,-0.205,4.6],[5.9,92.1,0.998,-0.061,4.6],[5.2,80.6,0.998,-0.061,4.6],[4.4,69.1,0.998,-0.061,4.6],[3.7,57.6,0.998,-0.061,4.6],[2.9,46.0,0.998,-0.06,4.6],[2.1,34.5,0.997,-0.075,4.6],[1.4,23.0,0.998,-0.066,4.6],[0.6,11.5,0.998,-0.066,4.6],[-0.1,0.0,0.998,-0.066,4.6],[-0.9,-11.5,0.998,-0.065,4.6],[-1.7,-23.0,0.997,-0.079,4.6],[-2.4,-34.5,0.998,-0.061,4.6],[-3.2,-46.0,0.998,-0.068,4.6],[-3.9,-57.5,0.998,-0.068,4.6],[-4.7,-69.0,0.998,-0.068,4.6],[-5.4,-80.6,0.998,-0.068,4.6],[-6.1,-92.1,0.998,-0.059,4.6],[-6.8,-103.6,0.998,-0.066,4.6],[-7.5,-115.1,0.998,-0.066,4.6],[-8.2,-126.6,0.998,-0.066,4.6],[-8.8,-138.1,0.998,-0.066,4.6],[-9.5,-149.6,0.998,-0.066,4.6],[-10.2,-161.1,0.999,-0.049,4.6],[-10.9,-172.7,0.999,-0.048,4.6]]},"SA":{"anchor":[-74.008955,40.731128],"ring":[[57.0,560.9],[53.2,492.3],[46.7,399.5],[42.0,321.2],[38.2,265.3],[36.0,245.5],[31.9,180.1],[28.9,155.8],[16.6,74.9],[7.5,10.5],[3.5,-5.0],[-14.6,-129.0],[-17.7,-164.3],[-29.2,-244.7],[-70.4,-525.7],[-73.9,-549.2],[-76.3,-559.2],[-85.2,-557.0],[-82.9,-547.5],[-79.5,-524.4],[-38.3,-243.4],[-26.9,-163.2],[-23.7,-127.9],[-5.5,-3.2],[-1.5,12.3],[7.5,76.3],[19.8,157.1],[22.8,181.2],[26.9,246.3],[29.0,266.1],[32.9,321.7],[37.5,400.1],[44.0,492.9],[47.8,561.2]],"par":[[[57.0,560.9],[53.2,492.3],[46.7,399.5],[42.0,321.2],[38.2,265.3],[36.0,245.5],[31.9,180.1],[28.9,155.8],[16.6,74.9],[7.5,10.5],[3.5,-5.0],[-14.6,-129.0],[-17.7,-164.3],[-29.2,-244.7],[-70.4,-525.7],[-73.9,-549.2],[-76.3,-559.2],[-85.2,-557.0],[-82.9,-547.5],[-79.5,-524.4],[-38.3,-243.4],[-26.9,-163.2],[-23.7,-127.9],[-5.5,-3.2],[-1.5,12.3],[7.5,76.3],[19.8,157.1],[22.8,181.2],[26.9,246.3],[29.0,266.1],[32.9,321.7],[37.5,400.1],[44.0,492.9],[47.8,561.2],[57.0,560.9]]],"spine":[[52.4,561.0],[37.5,321.5],[27.3,180.7],[3.0,11.4],[-1.0,-4.1],[-19.1,-128.5],[-22.3,-163.8],[-33.8,-244.0],[-74.9,-525.0],[-80.8,-558.1]],"bents":[[52.1,555.1,0.999,-0.046,4.6],[51.4,543.3,0.998,-0.057,4.6],[50.8,531.4,0.998,-0.057,4.6],[50.1,519.5,0.998,-0.057,4.6],[49.5,507.7,0.998,-0.057,4.6],[48.8,495.8,0.998,-0.058,4.6],[48.0,484.0,0.996,-0.085,4.6],[47.2,472.1,0.998,-0.064,4.6],[46.4,460.3,0.998,-0.064,4.6],[45.5,448.4,0.998,-0.064,4.6],[44.7,436.6,0.998,-0.064,4.6],[43.9,424.8,0.998,-0.064,4.6],[43.0,412.9,0.997,-0.083,4.6],[42.2,401.1,0.998,-0.065,4.6],[41.5,389.2,0.998,-0.057,4.6],[40.8,377.4,0.998,-0.057,4.6],[40.1,365.5,0.997,-0.071,4.6],[39.4,353.7,0.997,-0.071,4.6],[38.7,341.8,0.998,-0.065,4.6],[38.0,330.0,0.999,-0.051,4.6],[37.2,318.1,0.998,-0.069,4.6],[36.4,306.3,0.998,-0.069,4.6],[35.6,294.4,0.998,-0.069,4.6],[34.8,282.6,0.998,-0.069,4.6],[34.0,270.7,0.998,-0.069,4.6],[32.9,258.9,0.995,-0.103,4.6],[31.6,247.1,0.992,-0.125,4.6],[30.8,235.2,0.998,-0.061,4.6],[30.0,223.4,0.998,-0.061,4.6],[29.3,211.5,0.998,-0.06,4.6],[28.5,199.7,0.998,-0.06,4.6],[27.8,187.8,0.998,-0.061,4.6],[26.8,176.0,0.992,-0.126,4.6],[25.3,164.2,0.993,-0.121,4.6],[23.7,152.5,0.989,-0.148,4.6],[21.9,140.7,0.989,-0.148,4.6],[20.2,129.0,0.989,-0.148,4.6],[18.4,117.2,0.989,-0.148,4.6],[16.6,105.5,0.989,-0.148,4.6],[14.8,93.8,0.986,-0.165,4.6],[13.0,82.0,0.985,-0.173,4.6],[11.3,70.3,0.99,-0.14,4.6],[9.6,58.5,0.99,-0.14,4.6],[8.0,46.8,0.99,-0.14,4.6],[6.3,35.0,0.99,-0.14,4.6],[4.7,23.2,0.99,-0.14,4.6],[3.0,11.5,0.981,-0.196,4.6],[0.0,-0.0,0.97,-0.242,4.6],[-2.1,-11.7,0.99,-0.144,4.6],[-3.8,-23.4,0.99,-0.144,4.6],[-5.5,-35.2,0.99,-0.144,4.6],[-7.3,-46.9,0.99,-0.144,4.6],[-9.0,-58.7,0.99,-0.144,4.6],[-10.7,-70.4,0.99,-0.139,4.6],[-12.4,-82.2,0.989,-0.146,4.6],[-14.1,-93.9,0.99,-0.144,4.6],[-15.8,-105.7,0.99,-0.144,4.6],[-17.5,-117.4,0.99,-0.144,4.6],[-19.2,-129.2,0.994,-0.108,4.6],[-20.3,-141.0,0.995,-0.095,4.6],[-21.3,-152.8,0.998,-0.068,4.6],[-22.4,-164.7,0.991,-0.134,4.6],[-24.1,-176.4,0.99,-0.143,4.6],[-25.8,-188.2,0.99,-0.143,4.6],[-27.5,-199.9,0.989,-0.146,4.6],[-29.1,-211.7,0.989,-0.146,4.6],[-30.8,-223.4,0.989,-0.145,4.6],[-32.5,-235.2,0.992,-0.128,4.6],[-34.2,-246.9,0.989,-0.145,4.6],[-35.9,-258.7,0.989,-0.145,4.6],[-37.6,-270.4,0.989,-0.145,4.6],[-39.3,-282.2,0.989,-0.145,4.6],[-41.1,-293.9,0.989,-0.145,4.6],[-42.8,-305.7,0.989,-0.145,4.6],[-44.5,-317.4,0.989,-0.145,4.6],[-46.2,-329.2,0.989,-0.145,4.6],[-47.9,-340.9,0.989,-0.145,4.6],[-49.7,-352.7,0.989,-0.145,4.6],[-51.4,-364.4,0.989,-0.145,4.6],[-53.1,-376.2,0.989,-0.145,4.6],[-54.8,-387.9,0.989,-0.145,4.6],[-56.6,-399.7,0.989,-0.145,4.6],[-58.3,-411.4,0.989,-0.145,4.6],[-60.0,-423.2,0.989,-0.145,4.6],[-61.7,-434.9,0.989,-0.145,4.6],[-63.4,-446.7,0.989,-0.145,4.6],[-65.2,-458.4,0.989,-0.145,4.6],[-66.9,-470.2,0.989,-0.145,4.6],[-68.6,-481.9,0.989,-0.145,4.6],[-70.3,-493.7,0.989,-0.145,4.6],[-72.0,-505.4,0.989,-0.145,4.6],[-73.8,-517.2,0.989,-0.145,4.6],[-75.5,-528.9,0.989,-0.148,4.6],[-77.3,-540.7,0.989,-0.148,4.6],[-79.4,-552.3,0.972,-0.235,4.6]]},"SPUR":{"anchor":[-74.001124,40.752194],"line":[[16.2,-23.3],[14.4,-21.6],[12.2,-19.5],[10.6,-17.2],[9.0,-14.2],[5.3,-8.1],[-6.2,11.3],[-7.7,13.9],[-9.5,16.3],[-11.6,18.6],[-14.1,20.7],[-18.1,23.0]]},"CONN":{"anchor":[-74.000256,40.75194],"line":[[-57.0,4.8],[-52.4,13.7],[-48.9,11.8],[-46.3,16.4],[38.9,-26.0],[52.5,-32.8],[38.9,-26.0],[74.3,38.6]]},"DIME_W":[[-47.7,-54.6],[-53.9,-40.8],[-51.4,-39.7],[-31.0,-7.4],[-31.0,-54.9]],"DIME_E":[[-10.2,-10.3],[3.5,-37.3],[4.8,-37.4],[5.8,-35.7],[10.0,-36.0],[10.8,-36.0],[9.7,-55.7],[-31.0,-54.9],[-31.0,-7.4],[-18.6,12.3],[-9.0,-8.4]]};

// ====================================================================== The High Line
// Deck outline = the park's OpenStreetMap multipolygon (relation 7141751) clipped to the
// section, so the breadth is the real one (8-10 m, wider at the platforms); the centre line
// is the park's footways (ways 277885758 ... 1168715452) smoothed over 30 m. Deck level
// 9 m above the anchor's ground (the brief; OSM maps 7.5 m: estimated). Bents (two steel
// columns and a cross beam) every ~12 m: estimated spacing. South of Gansevoort Street the
// line is gone: it follows Washington Street (estimated).
const HL_Z = 9;
type HLSec = {anchor: V2; ring: V2[]; par: V2[][]; spine: V2[]; bents: number[][]};

function hlDeck(b: MeshBuilder, S: HLSec, kind: 'track' | 'park') {
  const steel = '#4B5752';
  b.color(kind === 'track' ? '#6E675E' : '#CFCBC2').prism(S.ring, HL_Z - 1.2, HL_Z);
  b.color(steel);
  for (const p of S.par) b.wallProfile(p, HL_Z, HL_Z + (kind === 'track' ? 0.8 : 1.1));
  for (const [x, y, nx, ny, hw] of S.bents) {
    const o = Math.max(hw - 0.9, 0.5);
    const a: V2 = [x + nx * o, y + ny * o];
    const c: V2 = [x - nx * o, y - ny * o];
    b.box(a[0], a[1], 0, 0.7, 0.7, HL_Z - 1.2).box(c[0], c[1], 0, 0.7, 0.7, HL_Z - 1.2);
    b.beam([a[0], a[1], HL_Z - 1.5], [c[0], c[1], HL_Z - 1.5], 0.5);
  }
  const sp = S.spine;
  for (let i = 0; i < sp.length - 1; i++) {
    const p = sp[i];
    const q = sp[i + 1];
    const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (L < 0.1) continue;
    const nx = -(q[1] - p[1]) / L;
    const ny = (q[0] - p[0]) / L;
    if (kind === 'track') {
      b.color('#5A544C').beam([p[0], p[1], HL_Z + 0.15], [q[0], q[1], HL_Z + 0.15], 3.4, 0.3);
      b.color('#2E2E30');
      for (const s of [-0.72, 0.72]) b.beam([p[0] + nx * s, p[1] + ny * s, HL_Z + 0.4], [q[0] + nx * s, q[1] + ny * s, HL_Z + 0.4], 0.14, 0.2);
    } else {
      b.color('#6F8C4F');
      for (const s of [-2.6, 2.6]) b.beam([p[0] + nx * s, p[1] + ny * s, HL_Z + 0.15], [q[0] + nx * s, q[1] + ny * s, HL_Z + 0.15], 1.8, 0.3);
    }
  }
}

/** A narrow footbridge along a line (Spur, Moynihan Connector). */
function hlLine(b: MeshBuilder, line: V2[], w: number, color: string, colEvery: number) {
  b.color(color);
  for (let i = 0; i < line.length - 1; i++) b.beam([line[i][0], line[i][1], HL_Z - 0.5], [line[i + 1][0], line[i + 1][1], HL_Z - 0.5], w, 1);
  b.color('#4B5752');
  let acc = 0;
  for (let i = 0; i < line.length - 1; i++) {
    const p = line[i];
    const q = line[i + 1];
    const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (L < 0.1) continue;
    const nx = -(q[1] - p[1]) / L;
    const ny = (q[0] - p[0]) / L;
    for (const s of [-1, 1]) b.beam([p[0] + nx * s * (w / 2 - 0.1), p[1] + ny * s * (w / 2 - 0.1), HL_Z + 0.6], [q[0] + nx * s * (w / 2 - 0.1), q[1] + ny * s * (w / 2 - 0.1), HL_Z + 0.6], 0.12, 1.1);
    acc += L;
    if (acc >= colEvery) {
      b.box(p[0], p[1], 0, 0.8, 0.8, HL_Z - 1);
      acc = 0;
    }
  }
}

const HL_SOURCES = [WIKI + 'High_Line', OSM + 'relation/7141751', OSM + 'way/1168715452', 'https://www.thehighline.org/history/'];
const HL_MODEL_TRACK = 'deck outline and breadth from OpenStreetMap relation 7141751, centre line from the park footways; deck level (9 m; OSM maps 7.5 m), bent spacing (12 m), columns and rails estimated';
const HL_MODEL_PARK = 'deck outline and breadth from OpenStreetMap relation 7141751, centre line from the park footways; deck level (9 m), railing, planting strips (2 x 1.8 m) and bent spacing estimated';

function hlTrack(id: string, name: string, key: string, built: [number, number], end: number, facts: Record<string, string>, model = HL_MODEL_TRACK): Landmark {
  const S = HL[key] as HLSec;
  return {id, name, kind: 'building', built, end, anchor: S.anchor, build: b => hlDeck(b, S, 'track'), facts: {...facts, Model: model}, sources: HL_SOURCES};
}
function hlPark(id: string, name: string, key: string, built: [number, number], end: number, facts: Record<string, string>): Landmark {
  const S = HL[key] as HLSec;
  return {id, name, kind: 'park', built, end, anchor: S.anchor, build: b => hlDeck(b, S, 'park'), facts: {...facts, Model: HL_MODEL_PARK}, sources: HL_SOURCES};
}

const HL_BUILT: [number, number] = [1932.0, 1934.49];
const HL_OPEN = "Dedicated 29 June 1934 (first train in 1933): the West Side Improvement's freight viaduct of the New York Central, 35th Street to the St. John's Park Freight Terminal at Spring Street; 1.45 mi of it survives";

MORE_A.push(
  hlTrack('high_line_spring_bank', 'West Side freight viaduct (Bank to Spring Street)', 'SA', HL_BUILT, 1961.0, {
    Opened: HL_OPEN,
    Gone: "the St. John's terminal was abandoned in 1960 and the southernmost section, Bank Street down Washington Street to Spring Street, came down in the 1960s (the article gives no year: 1961 estimated)",
    Route: 'Washington Street (estimated line: the sources describe the route, no survey was found)'
  }, "line follows Washington Street from OpenStreetMap, deck breadth (9.2 m, the park's median) and deck level (9 m) estimated; the terminal building is not modelled"),
  hlTrack('high_line_bank_gansevoort', 'West Side freight viaduct (Gansevoort to Bank Street)', 'SB', HL_BUILT, 1991.0, {
    Opened: HL_OPEN,
    Gone: 'taken down in 1991 (Gansevoort Street to Bank Street)',
    Route: 'Washington Street (estimated line)'
  }, 'line follows Washington Street from OpenStreetMap, deck breadth (9.2 m) and deck level (9 m) estimated'),
  hlTrack('high_line_viaduct_1', 'High Line viaduct (Gansevoort to 20th Street)', 'S1', HL_BUILT, 2006.3, {
    Opened: HL_OPEN,
    Closed: 'Conrail disconnected the viaduct from the rail network in 1980 (the last train carried frozen turkeys); works for the park began in 2006 (estimated 2006.3)'
  }),
  hlTrack('high_line_viaduct_2', 'High Line viaduct (20th to 30th Street)', 'S2', HL_BUILT, 2009.7, {
    Opened: HL_OPEN,
    Closed: 'derelict from 1980; works for the second section began in 2009 (estimated 2009.7)'
  }),
  hlTrack('high_line_viaduct_3', 'High Line viaduct (30th to 34th Street, the rail yards)', 'S3', HL_BUILT, 2012.7, {
    Opened: HL_OPEN,
    Closed: 'derelict from 1980; works for the third section began in 2012 (estimated 2012.7)'
  }),
  hlPark('high_line_park_1', 'The High Line (Gansevoort to 20th Street)', 'S1', [2006.3, 2009.43], 9999, {
    Opened: '8 June 2009 (Section 1, Gansevoort Street to 20th Street); works from 2006 (estimated)',
    Designers: 'James Corner Field Operations with Diller Scofidio + Renfro and Piet Oudolf'
  }),
  hlPark('high_line_park_2', 'The High Line (20th to 30th Street)', 'S2', [2009.7, 2011.43], 9999, {
    Opened: '7 June 2011 (Section 2, 20th Street to 30th Street)'
  }),
  hlPark('high_line_park_3', 'The High Line at the Rail Yards (30th to 34th Street)', 'S3', [2012.7, 2014.72], 9999, {
    Opened: '21 September 2014 (Section 3, around the Hudson Yards rail yards to 34th Street)'
  })
);
{
  const Sp = HL.SPUR as {anchor: V2; line: V2[]};
  const Cn = HL.CONN as {anchor: V2; line: V2[]};
  MORE_A.push(
    {
      id: 'high_line_spur',
      name: 'The High Line, Tenth Avenue Spur',
      kind: 'park',
      built: [2017.5, 2019.43],
      end: 9999,
      anchor: Sp.anchor,
      build: b => hlLine(b, Sp.line, 7, '#CFCBC2', 14),
      facts: {Opened: '4 June 2019: the spur over 30th Street towards Tenth Avenue, with the plinth (first artwork) and entrances to 10 Hudson Yards', Model: 'line from OpenStreetMap way 1185582162; breadth (7 m), deck level (9 m), works start (2017.5) estimated'},
      sources: [WIKI + 'High_Line', OSM + 'way/1185582162']
    },
    {
      id: 'high_line_moynihan_connector',
      name: 'Moynihan Connector (High Line)',
      kind: 'park',
      built: [2022.0, 2023.47],
      end: 9999,
      anchor: Cn.anchor,
      build: b => hlLine(b, Cn.line, 3.6, '#B8B2A6', 12),
      facts: {Opened: 'June 2023 (22 June): 1,200 ft from the Spur along 30th Street to Dyer Avenue, then north to 31st Street and Manhattan West; the Woodlands Bridge over 30th Street and the Timber Bridge', Model: 'line from OpenStreetMap ways 1185582164, 1021481785, 1080012421 (the 14 m gap between them closed by a straight link); breadth (3.6 m), deck level (9 m), works start (2022) estimated'},
      sources: [WIKI + 'High_Line', OSM + 'way/1021481785']
    }
  );
}

// ====================================================================== James A. Farley Building
// Frame at the anchor, +y at 29.1 deg (the avenues); +x points to Eighth Avenue (u = +114 m),
// Ninth Avenue is at u = -114. The block outline is OpenStreetMap way 264667030 (228 x 117 m).
// The 1914 building occupies the Eighth Avenue 101 m (332 ft), the annex of 1935 the rest.
const FARLEY: V2 = [-73.99589, 40.75154];
const F_B = 29.1;
const F_V0 = -57.6;
const F_V1 = 56.5;
const F_ROOF = 31;
const F_COURT = 27;
const F_CT: V2[] = rect(61.5, 0, 47.4, 69.0);
function farleyBlockReplaces(): V2[][] {
  const a = (F_B * Math.PI) / 180;
  const u = 0.4;
  const v = 0.05;
  return [rotRect(u * Math.cos(a) + v * Math.sin(a), -u * Math.sin(a) + v * Math.cos(a), 228.2, 117.5, F_B)];
}

function buildFarley1914(b: MeshBuilder) {
  const granite = '#CFC6B4';
  const cx = (13.5 + 108.5) / 2;
  const cy = (F_V0 + F_V1) / 2;
  const sx = 108.5 - 13.5;
  const sy = F_V1 - F_V0;
  b.frame(0, 0, 0, F_B, () => {
    b.color(granite).prism(rect(cx, cy, sx, sy), 0, F_COURT);
    // upper ring around the sorting-room court (the court roof stays at 27 m)
    b.color('#C4BBA8').prism(rect(cx, cy, sx, sy), F_COURT, F_ROOF, {holes: [F_CT]});
    b.color('#B7AE9B').box(cx, cy, F_ROOF, sx + 0.8, sy + 0.8, 0.5);
    // end pavilions with pyramidal roofs
    for (const v of [-49.6, 48.5]) {
      b.color(granite).box(111, v, 0, 5, 16.5, 24.5);
      b.color('#8E8A80').pyramid(rect(111, v, 5.4, 17.2), 24.5, [111, v, 31]);
    }
    // stylobate, steps (six runs for the 31 steps) and the 20-column Corinthian colonnade, 53 ft (16 m)
    b.color('#D8D1C1');
    for (let k = 0; k < 6; k++) b.box(112.4 + k * 0.4, 0, 0, 3.4 - k * 0.8, 81, 0.8 * (k + 1) - 0.2);
    b.box(111, 0, 0, 3.4, 81, 4.6);
    b.color('#E4DDCC');
    for (let k = 0; k < 20; k++) b.cylinder(111, -38.2 + k * 4.02, 0.8, 4.6, 20.6, 10);
    b.color('#D2CBBA').box(110.6, 0, 20.6, 4.4, 81, 3.8);
    b.color(granite).box(107.5, 0, 24.4, 2, 81, 6.6);
  });
}

function buildFarleyAnnex(b: MeshBuilder) {
  b.frame(0, 0, 0, F_B, () => {
    b.color('#C9C0AE').prism(rect(-50.2, (F_V0 + F_V1) / 2, 127.4, F_V1 - F_V0), 0, F_ROOF);
    b.color('#B7AE9B').box(-50.2, (F_V0 + F_V1) / 2, F_ROOF, 128.2, F_V1 - F_V0 + 0.8, 0.5);
    b.color('#A8A294');
    for (const dv of [-1, 1]) for (let k = 0; k < 12; k++) b.box(-103 + k * 10, dv * (F_V1 - 0.1), 4, 2.2, 0.5, 22);
  });
}

function buildMoynihanHall(b: MeshBuilder) {
  // four glass vaults over the old mail-sorting court (OSM bays: 47.4 m long, 69 m across)
  const bays = [-34.5, -13.65, 0.8, 15.8, 34.5];
  b.frame(0, 0, 0, F_B, () => {
    b.color('#6D7378').box(61.5, 0, F_COURT, 49, 70.6, 1.4, {top: false});
    for (let i = 0; i < 4; i++) {
      const c = (bays[i] + bays[i + 1]) / 2;
      const w = bays[i + 1] - bays[i];
      b.color('#A9CDD8').gable(61.5, c, 47.4, w, F_COURT + 1.4, 3.7, false);
      b.color('#5B6368');
      b.beam([37.8, c, F_COURT + 1.4], [61.5, c, F_COURT + 5.1], 0.4);
      b.beam([85.2, c, F_COURT + 1.4], [61.5, c, F_COURT + 5.1], 0.4);
    }
    for (const v of bays) b.beam([37.8, v, F_COURT + 1.4], [85.2, v, F_COURT + 1.4], 0.5, 1.2);
  });
}

const F_SOURCES = [WIKI + 'James_A._Farley_Building', WIKI + 'Moynihan_Train_Hall', OSM + 'way/264667030', FOOTPRINTS];
MORE_A.push(
  {
    id: 'farley_post_office_1914',
    name: 'General Post Office (James A. Farley Building), 1914',
    kind: 'building',
    built: [1911.2, 1914.68],
    end: 9999,
    anchor: FARLEY,
    build: buildFarley1914,
    replaces: farleyBlockReplaces(),
    facts: {
      Built: 'contract March 1911 (George A. Fuller Co.), opened 5 September 1914; McKim, Mead & White (William Mitchell Kendall)',
      Size: '355 ft on Eighth Avenue, 332 ft on the side streets; four storeys of granite on a steel frame, roof about 101 ft (31 m) above the curb',
      'Eighth Avenue': 'twenty Corinthian columns 53 ft (16 m) high over a flight of 31 steps, end pavilions with pyramidal roofs',
      Model: 'block outline from OpenStreetMap (228 x 117 m), roof 31 m (city-measured 31.2 m), column count and height cited; the 332 ft depth of the 1914 part, step depths, pavilion size, the 27 m roof of the sorting-room court and the cornice (removed in 1994, drawn) estimated'
    },
    sources: F_SOURCES
  },
  {
    id: 'farley_annex_1935',
    name: 'General Post Office, western annex (1935)',
    kind: 'building',
    built: [1932.5, 1935.95],
    end: 9999,
    anchor: FARLEY,
    build: buildFarleyAnnex,
    facts: {
      Built: 'the Treasury bought the western half of the block from the Pennsylvania Railroad in 1931; built 1932-1935 ($4.3 million contract to James Stewart & Co., February 1934), opened December 1935',
      Size: 'the western half of the block to Ninth Avenue; whole site 455 x 800 ft, roof about 31 m',
      Model: 'outline from OpenStreetMap; roof 31 m from OSM parts; the pilasters on the long sides and the width of the annex (the part west of the 1914 building) estimated'
    },
    sources: F_SOURCES
  },
  {
    id: 'moynihan_train_hall',
    name: 'Moynihan Train Hall (skylights over the Farley Building)',
    kind: 'building',
    built: [2017.6, 2021.0],
    end: 9999,
    anchor: FARLEY,
    build: buildMoynihanHall,
    facts: {
      Built: 'second phase begun about August 2017 (the first phase, new exits and concourse, opened June 2017); opened 1 January 2021; Skidmore, Owings & Merrill',
      Size: 'about 255,000 sq ft in all, the hall about 31,000 sq ft under a glass skylight 92 ft (28 m) tall',
      Model: 'court outline (47.4 x 69 m) and the four bays from OpenStreetMap parts; the vault shape and its rise (3.7 m above a 28.4 m deck, crest 32 m as mapped) are a simplification of the steel-truss skylights'
    },
    sources: F_SOURCES
  }
);

// ====================================================================== Brooklyn Tower and the Dime
// Anchor on the tower (OSM part 1039403183, the hexagon). The Dime Savings Bank's outline is
// OSM part 248156228 (the bank as enlarged); the city's footprint (BIN 3000370) is the union.
const TOWER_ANCHOR: V2 = [-73.98228, 40.69056];
const HEX: V2[] = [[-14.3, 4.8], [-3.6, -16.4], [11.5, -17.1], [19.4, -4.4], [8.9, 14.6], [-6.6, 15.4]];
const HEX_C: V2 = [2.6, -0.8];
function scaled(r: V2[], s: number): V2[] {
  return r.map(p => [HEX_C[0] + (p[0] - HEX_C[0]) * s, HEX_C[1] + (p[1] - HEX_C[1]) * s] as V2);
}

function buildBrooklynTower(b: MeshBuilder) {
  const roof = 315.5;
  const stages = 8;
  for (let i = 0; i < stages; i++) {
    const z0 = (roof * i) / stages;
    const z1 = (roof * (i + 1)) / stages;
    b.color(i < 1 ? '#8A857C' : i % 2 ? '#4A4B58' : '#52535F').prism(scaled(HEX, 1 - 0.011 * i), z0, z1);
  }
  // crown: three narrowing steps up to the 325 m top
  const s0 = 1 - 0.011 * (stages - 1) - 0.02;
  b.color('#3F4049').prism(scaled(HEX, s0), roof, roof + 3.2);
  b.color('#3F4049').prism(scaled(HEX, s0 * 0.78), roof + 3.2, roof + 6.4);
  b.color('#2C2D34').prism(scaled(HEX, s0 * 0.55), roof + 6.4, 325);
}

function dimeBody(b: MeshBuilder, ring: V2[]) {
  b.color('#EDE8DC').prism(ring, 0, 24);
  b.color('#D9D3C4').prism(ring, 24, 25.2);
  b.color('#B97F83').prism(ring, 0, 1.6, {top: false});
}

function buildDime1908(b: MeshBuilder) {
  dimeBody(b, HL.DIME_W as V2[]);
}

function buildDime1932(b: MeshBuilder) {
  dimeBody(b, HL.DIME_E as V2[]);
  // the rotunda's roof: hexagonal tholobate and marble dome (OSM part 700241894: centre
  // (-20.9, -35.5), radius 10.3 m; top 33.3 m)
  const cx = -20.9;
  const cy = -35.5;
  b.color('#EDE8DC').cylinder(cx, cy, 10.3, 25.2, 28.6, 6);
  b.color('#D9D3C4').cylinder(cx, cy, 10.7, 28.6, 29.4, 6);
  b.color('#E2DDCF').dome(cx, cy, 10.3, 29.4, 3.9, 18, 4);
}

const T_SOURCES = [WIKI + '9_DeKalb_Avenue', OSM + 'way/1229206093', OSM + 'way/248156228', FOOTPRINTS];
MORE_A.push(
  {
    id: 'dime_savings_bank_1908',
    name: 'Dime Savings Bank of Brooklyn (1908)',
    kind: 'building',
    built: [1906.5, 1908.97],
    end: 9999,
    anchor: TOWER_ANCHOR,
    build: buildDime1908,
    facts: {
      Built: '1906-1908 by Mowbray & Uffinger; opened 19 December 1908. White Pentelic marble (about 2,000 tons) over a pink granite water table, the first U.S. bank so clad',
      Size: 'originally about 114 ft on Fleet Street, 30 ft on Albee Square and 143 ft on DeKalb Avenue',
      Model: 'the corner of the enlarged outline (OSM part 248156228) west of x = -31 m stands for the original lot (which part was the original is not published: estimated); the 24 m cornice height and the plain roof are estimated'
    },
    sources: T_SOURCES
  },
  {
    id: 'dime_savings_bank_1932',
    name: 'Dime Savings Bank of Brooklyn (enlarged 1932)',
    kind: 'building',
    built: [1931.0, 1932.7],
    end: 9999,
    anchor: TOWER_ANCHOR,
    build: buildDime1932,
    facts: {
      Built: '1931-1932 by Halsey, McCormack & Helmer: the enlargement added the hexagonal rotunda (twelve red marble columns, sky-blue dome); now the base of the Brooklyn Tower (city landmark, facade and interior)',
      Size: 'enlarged to about 202 ft on Fleet Street, 47 ft on Albee Square, 173 ft on DeKalb Avenue; banking hall 16,750 sq ft under a 40 ft ceiling',
      Model: 'outline east of x = -31 m from OSM part 248156228 (the whole bank is 2,400 m2, the city footprint 2,417 m2); dome centre, radius and top height (33.3 m) from OSM, the 24 m cornice and the tholobate height estimated'
    },
    sources: T_SOURCES
  },
  {
    id: 'brooklyn_tower',
    name: 'The Brooklyn Tower (9 DeKalb Avenue)',
    kind: 'tower',
    built: [2018.5, 2022.3],
    end: 9999,
    anchor: TOWER_ANCHOR,
    build: buildBrooklynTower,
    facts: {
      Built: 'construction from 2018, topped out 28 October 2021, opened 2022; SHoP Architects, structural engineer WSP',
      Height: '1,066 ft (325 m) to the crown (the city measures the main roof at 315.5 m; other sources give 1,035 ft to the roof and 1,073 ft to the FAA crown)',
      Form: "a hexagonal tower of 74 floors (some sources count 93) with slight setbacks on each side ending in a crown, after the hexagon of the Dime's banking hall; 555,734 sq ft",
      Model: "hexagonal plan from OpenStreetMap part 1039403183; roof 315.5 m (city-measured, BIN 3000370) and crown top 325 m cited; the setbacks (1.1 % of the plan per 39 m), their heights, the crown's three steps and the facade colours are estimates"
    },
    sources: T_SOURCES
  }
);
