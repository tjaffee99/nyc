/**
 * New York landmarks, second pass B: towers and apartment houses that stand today and were missing.
 * Research, sources and numeric checks: data/research/landmarks_more_b.md.
 *
 * Same conventions as nyc-towers.ts: each model is drawn in the building's own frame (origin =
 * centroid of the city's official footprint, +v along the bearing `B` of the long edge); plans
 * come from the official footprint (NYC building footprints), set-back levels from OpenStreetMap
 * building parts where volunteers mapped them (© OpenStreetMap contributors, ODbL, via Overture
 * 2026-10-21.0); total heights from the cited sources. What is estimated is named in each
 * model's `Model:` fact.
 */
import {MeshBuilder, type V2} from './kit';
import type {Landmark} from './types';

type Level = [number, number, V2[]];
type Massing = {anchor: V2; B: number; foot: V2[][]; levels: Level[]};

// <massing> (data/interim/landmarks_more_b/gen.py; hand-set entries below the generated ones)
const M: Record<string, Massing> = {
  one57: {
    anchor: [-73.979016, 40.765515],
    B: 29.1,
    foot: [[[-17.0, -24.9], [-17.0, 12.1], [-22.5, 11.9], [-22.0, 35.8], [0.9, 36.2], [0.9, 5.5], [11.5, 5.6], [11.5, -3.5], [31.5, -3.5], [31.5, -24.8]]],
    levels: [
      [0, 30, [[-17.0, -24.9], [-17.0, 3.3], [-17.0, 10.1], [-17.0, 12.1], [-22.1, 11.9], [-22.5, 11.9], [-22.0, 35.8], [0.9, 36.2], [0.9, 24.4], [0.9, 5.5], [11.5, 5.6], [11.5, -3.5], [29.5, -3.5], [31.5, -3.5], [31.5, -6.5], [31.5, -22.6], [31.5, -22.8], [31.5, -24.8], [29.3, -24.8]]],
      [30, 35, [[-20.3, -25.9], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -25.7]]],
      [35, 45, [[-20.3, -25.9], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1], [-7.3, -22.2], [-7.6, -25.8]]],
      [45, 95, [[-20.3, -22.2], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1]]],
      [95, 119.8, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -22.1], [6.0, -22.2], [5.9, -18.6], [-5.1, -18.6], [-5.3, -15.3]]],
      [119.8, 125, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.7, -3.6], [30.9, -3.4], [30.8, -15.3], [22.2, -15.3], [22.0, -18.5], [-5.1, -18.6], [-5.4, -15.3]]],
      [125, 226.8, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.6, -3.6], [22.0, -3.4], [22.0, -18.5], [-5.1, -18.6], [-5.4, -15.3]]],
      [226.8, 230, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.6, -3.6], [22.0, -3.4], [22.0, -15.3]]],
      [230, 298.6, [[-20.2, -15.3], [-20.2, 19.8], [0.5, 19.9], [0.5, -3.4], [9.1, -3.5], [9.1, -15.2]]],
      [298.6, 306, [[-20.2, -3.7], [-20.2, 19.8], [0.5, 19.9], [0.5, -3.6]]],
    ]
  },

  twc: {
    anchor: [-73.983098, 40.768476],
    B: 29.0,
    foot: [[[50.2, 37.7], [45.7, 23.6], [41.5, 23.7], [41.0, -2.8], [45.6, -2.9], [47.7, -10.6], [51.5, -19.8], [56.8, -28.3], [61.9, -34.5], [66.1, -38.6], [72.4, -43.6], [79.3, -47.7], [86.5, -51.0], [85.2, -54.7], [94.5, -55.9], [94.5, -59.3], [-54.2, -59.4], [-53.9, 67.7], [32.8, 67.8]]],
    levels: [
      [0, 45, [[50.2, 37.7], [45.7, 23.6], [41.5, 23.7], [41.0, -2.8], [45.6, -2.9], [46.0, -4.9], [46.5, -6.8], [47.0, -8.7], [47.7, -10.6], [48.3, -12.5], [49.0, -14.4], [49.8, -16.2], [50.6, -18.0], [50.8, -18.3], [51.5, -19.8], [52.5, -21.6], [53.5, -23.3], [54.5, -25.0], [55.6, -26.7], [56.8, -28.3], [58.0, -29.9], [59.2, -31.5], [60.5, -33.0], [61.9, -34.5], [63.2, -35.9], [64.7, -37.3], [66.1, -38.6], [67.7, -39.9], [69.2, -41.2], [70.8, -42.4], [72.4, -43.6], [74.1, -44.7], [75.8, -45.7], [76.0, -45.9], [77.5, -46.8], [79.3, -47.7], [81.0, -48.6], [82.9, -49.5], [84.7, -50.3], [86.5, -51.0], [86.1, -52.2], [85.3, -54.3], [85.2, -54.7], [94.5, -55.9], [94.5, -59.1], [94.5, -59.3], [64.5, -59.3], [47.9, -59.3], [17.0, -59.3], [6.8, -59.3], [0.3, -59.3], [-28.4, -59.3], [-54.2, -59.4], [-54.2, -57.6], [-54.1, -43.5], [-54.1, -24.1], [-54.0, 29.7], [-53.9, 51.7], [-53.9, 58.0], [-53.9, 63.1], [-53.9, 67.7], [-13.0, 67.7], [32.8, 67.8], [49.5, 39.0]]],
      [45, 55, [[-44.8, -3.4], [-44.0, 59.8], [-31.0, 59.7], [-30.9, 64.6], [30.1, 63.1], [11.9, 23.8], [16.1, -3.8], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7], [-40.3, -3.7]]],
      [55, 80, [[-40.3, -3.4], [16.1, -3.9], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7]]],
      [55, 80, [[-44.3, 25.3], [-44.0, 59.8], [-31.0, 59.7], [-30.9, 64.6], [30.1, 63.1], [11.9, 23.7]]],
      [80, 105, [[-40.3, -3.4], [16.1, -3.9], [16.9, -5.0], [20.5, -5.1], [59.8, -46.3], [-40.1, -45.7]]],
      [80, 105, [[-44.3, 25.3], [-44.0, 59.8], [20.9, 59.3], [11.9, 23.7]]],
      [105, 125, [[-40.3, -3.4], [16.1, -3.9], [36.8, -38.3], [-40.1, -38.2]]],
      [105, 125, [[-44.0, 59.8], [-19.4, 59.0], [0.5, 24.5], [-24.0, 25.0]]],
      [125, 230, [[-13.1, -3.6], [16.1, -3.9], [36.8, -38.3], [7.0, -38.2]]],
      [125, 230, [[-44.0, 59.8], [-19.4, 59.0], [0.5, 24.5], [-24.0, 25.0]]],
    ]
  },

  hy35: {
    anchor: [-74.000108, 40.75453],
    B: 28.7,
    foot: [[[46.7, -23.3], [-46.6, -23.2], [-46.6, 23.2], [46.6, 23.2]]],
    levels: [
      [0, 33, [[46.7, -23.3], [-46.6, -23.2], [-46.6, 23.2], [46.6, 23.2]]],
      [33, 160, [[-45.7, -25.0], [-45.6, 23.6], [48.5, 23.8], [48.4, -24.7]]],
      [160, 308, [[-27.3, -24.9], [-27.2, 23.6], [48.5, 23.8], [48.4, -24.7]]],
    ]
  },

  w53: {anchor: [-73.978162, 40.761825], B: 29.0, foot: [[[-12.0, 29.0], [20.9, 29.1], [20.8, 10.8], [13.1, 10.8], [13.1, 5.9], [20.8, 5.9], [20.8, -1.4], [8.5, -1.4], [8.5, -31.9], [-18.0, -32.0], [-18.0, -1.5], [-12.0, -1.5]]], levels: []},
  plaza: {anchor: [-73.974449, 40.764456], B: 28.1, foot: [[[-48.4, -28.3], [-48.3, 1.0], [-33.9, 1.0], [-33.9, 21.4], [-36.3, 21.4], [-36.3, 33.8], [39.1, 33.8], [41.9, 30.5], [41.8, -29.6], [39.0, -31.4], [-42.9, -31.4], [-42.9, -28.3]]], levels: [[58, 64, [[-46.9, -26.8], [-46.8, -0.5], [-32.4, -0.5], [-32.4, 22.9], [-34.8, 22.9], [-34.8, 32.3], [38.4, 32.3], [40.4, 30.0], [40.3, -28.8], [38.6, -29.9], [-41.4, -29.9], [-41.4, -26.8]]], [64, 70, [[-45.2, -25.1], [-45.1, -2.2], [-30.7, -2.2], [-30.7, 24.6], [-33.1, 24.6], [-33.1, 30.6], [37.6, 30.6], [38.7, 29.3], [38.6, -27.9], [38.1, -28.2], [-39.7, -28.2], [-39.7, -25.1]]], [70, 76.8, [[-43.4, -23.3], [-43.3, -4.0], [-28.9, -4.0], [-28.9, 26.4], [-31.3, 26.4], [-31.3, 28.8], [36.9, 28.7], [36.8, -26.4], [-37.9, -26.4], [-37.9, -23.3]]]]},
  carnegie: {anchor: [-73.979914, 40.765004], B: 29.2, foot: [[[-22.9, 30.5], [23.0, 30.6], [22.9, -30.0], [16.6, -30.1], [16.6, -30.7], [-22.9, -30.7]]], levels: []},
  ansonia: {anchor: [-73.980849, 40.780515], B: 28.7, foot: [[[28.6, -23.5], [-21.5, -23.5], [-35.1, 21.7], [28.6, 21.7]]], levels: [[61, 67, [[27.4, -22.3], [-20.6, -22.3], [-33.5, 20.5], [27.4, 20.5]]], [67, 73, [[25.6, -20.5], [-19.3, -20.5], [-31.1, 18.7], [25.6, 18.7]]], [73, 78, [[23.6, -18.5], [-17.8, -18.5], [-28.4, 16.7], [23.6, 16.7]]]]},
  dakota: {anchor: [-73.97615, 40.776784], B: 29.1, foot: [[[-31.3, 31.3], [30.3, 31.3], [30.2, -8.0], [29.1, -8.0], [29.1, -16.5], [30.1, -16.5], [30.1, -31.6], [-31.2, -31.6], [-31.1, -15.2], [-28.9, -15.2], [-28.8, 14.8], [-31.3, 14.8]]], levels: [[0, 36, [[-7.2, 8.2], [-7.3, -8.8], [-12.8, -8.8], [-12.8, -15.5], [12.1, -15.5], [12.1, -8.2], [5.7, -8.2], [5.8, 8.1], [12.2, 8.1], [12.2, 14.5], [-11.9, 14.5], [-13.3, 12.6], [-11.9, 8.2]]]]},
  javits: {anchor: [-74.0025, 40.7578], B: 28.9, foot: [[[-110.4, 130.8], [98.4, 130.8], [98.1, -5.8], [121.8, -5.8], [125.3, -9.4], [125.1, -88.3], [121.6, -91.7], [97.8, -91.7], [97.7, -146.1], [-110.9, -146.2]]], levels: []},
  javits_x: {anchor: [-74.0025, 40.7578], B: 28.9, foot: [[[-42.2, 130.9], [-42.1, 158], [98.4, 158.1], [98.4, 130.8], [-76.3, 130.8]]], levels: []},
  oculus: {anchor: [-74.0114, 40.7115], B: 38.1, foot: [[[-49.2, 9], [-38.6, 11.8], [-17, 16], [4, 16.1], [24.6, 13.6], [24.5, 15.7], [29.8, 16.1], [44.4, 11.8], [46.2, 7.6], [51.6, 4.4], [53.2, 1.9], [53.3, -1], [51.1, -6.1], [44.7, -11.3], [28.7, -16], [21.7, -17.2], [21.1, -14.1], [10.4, -16.1], [-1.9, -16.3], [-16, -15.4], [-38, -11.5], [-49, -7.5], [-50, -7.8], [-52.7, -6.3], [-55.3, -3.9], [-56.5, -0], [-56, 3.5], [-53.7, 6.9]]], levels: []},
  whitney: {anchor: [-74.009, 40.7396], B: 3.7, foot: [[[6.1, 24], [15.7, 24.1], [15.8, 9.5], [43.8, 9.9], [43.8, 4.5], [41.1, 4.5], [41.1, -16.6], [-41.4, -16.6], [-41.4, 5.2], [-32.4, 5.2], [-32.4, 11.4], [-29.2, 14.9], [-23.9, 11.2], [-16.8, 21.8], [6.1, 21.8]]], levels: []},
  cloisters: {anchor: [-73.9319, 40.8648], B: 19.3, foot: [[[20.1, 13.8], [20.1, -3.1], [23.3, -3.1], [23.3, -12.6], [22.3, -12.6], [22.3, -42], [2.6, -42], [2.6, -41], [-19, -41.1], [-19, -28.9], [-22.2, -28.9], [-24.6, -26.7], [-24.6, -14], [-26.2, -14], [-25.7, 16.2], [-28.9, 17.5], [-29.9, 20.1], [-29.1, 22.4], [-27.1, 23.7], [-17.2, 23.8], [-17.2, 40.4], [-4.5, 40.4], [-4.1, 45], [-2.3, 48.5], [0.6, 50], [3.8, 49.3], [5.3, 47.7], [6, 45], [6.5, 45], [6.9, 35.8], [20.6, 35.6], [20.6, 29.9], [19.3, 29.9], [19.3, 26.7], [20.3, 26], [20.6, 24.8], [35.7, 24.4], [35.7, 14.4], [18.1, 14.4], [18.1, 13.8]]], levels: []},
  twa: {anchor: [-73.7777, 40.6458], B: -5.2, foot: [[[30.4, -20.8], [25.3, -27.6], [16.9, -34.7], [30.6, -46.3], [22.5, -54.1], [16.5, -58.8], [5.7, -65], [0.4, -62], [-2.4, -66.3], [-7.3, -63.3], [-12.4, -71.2], [-15.2, -69.6], [-16.6, -71.8], [-23, -67.9], [-24.2, -68.9], [-27.4, -69.9], [-34.7, -71.1], [-39.1, -70.9], [-44, -69.4], [-39, -65.1], [-31.2, -52.7], [-24.7, -39.1], [-17.7, -17.8], [-14.9, -14.6], [-16.1, -9.2], [-20.4, -4.5], [-26.3, 4.4], [-28, 4.7], [-28.2, 5.6], [-27, 5.5], [-25.9, 6.3], [-21.2, 13.6], [-16.8, 18.8], [-17.8, 24.4], [-15.8, 22.2], [-15.1, 25.8], [-18.1, 29.3], [-22.9, 45.1], [-29.7, 60.4], [-36.6, 72.1], [-41.4, 78.1], [-44, 79.4], [-43.1, 80.2], [-38.3, 81.5], [-28.5, 81], [-23.2, 79.4], [-11.9, 73.5], [-6.2, 69.4], [-0.5, 64.2], [13.5, 46.7], [23.5, 39.7], [27.1, 36.6], [30.4, 32.2], [37.6, 17.5], [40.6, 6], [39.6, 0], [36.3, -10.1]]], levels: []},
  apollo: {anchor: [-73.9499, 40.8102], B: 28.8, foot: [[[1.1, -1.9], [1.1, -36.3], [-13.5, -36.4], [-13.5, 23.9], [20.6, 23.9], [20.6, -1.9]]], levels: []},
  sanremo: {anchor: [-73.9751, 40.778], B: 29, foot: [[[20.3, 31.4], [20.3, -30], [-24.8, -30.1], [-24.8, -12.3], [-21.1, -12.3], [-21.1, -4.1], [-4.9, -4.1], [-4.9, -13.3], [3.7, -13.2], [3.7, 14.4], [-5.6, 14.4], [-5.6, 5.5], [-18.4, 5.5], [-18.4, 13.7], [-21.6, 13.7], [-21.6, 31.3]]], levels: []},
  bpl: {anchor: [-73.9681, 40.6722], B: 16.3, foot: [[[35.1, 58.4], [38.4, 42.5], [12.3, 37.6], [14.3, 27.6], [18.5, 28.5], [19, 19.5], [27.6, 19.2], [26.9, 11], [25.2, 3.1], [19.8, -10.1], [16.6, -15.3], [9.8, -10.8], [5.3, -16.5], [2.1, -13.3], [-5.3, -20.7], [10.8, -36.7], [13.4, -34.1], [13.3, -28.9], [37.1, -28.4], [38.3, -57.5], [37.7, -57.8], [37.4, -62.7], [36, -65.6], [33.1, -68.5], [30.2, -69.9], [26.1, -70.3], [22.2, -69.1], [18.6, -65.9], [18.2, -66.3], [-48.3, -0.4], [-43.6, 3.6], [-39.6, 8.4], [-36.4, 13.8], [-34.2, 19.6], [-32.9, 25.7], [-32.7, 31.9], [-33.5, 38.1], [-35.3, 44]]], levels: []},
  queens: {anchor: [-73.8467, 40.7459], B: -22.4, foot: [[[23.6, 63.9], [23.7, 57.7], [33, 57.7], [33, 52.1], [30.3, 50.2], [29.2, 47], [30.1, 44.2], [32.8, 42.1], [32.8, 35.9], [26.9, 35.9], [27.3, -35.9], [33, -35.9], [33, -41.7], [30.4, -43.9], [29.6, -46.6], [30.3, -49.4], [32.9, -51.7], [32.9, -57.6], [23.9, -57.6], [24, -63.8], [-25.7, -64], [-25.7, -57.5], [-32.5, -57.5], [-32.6, -51.9], [-30.3, -50], [-29.4, -46.6], [-30.3, -43.8], [-32.6, -41.9], [-32.6, -35.8], [-26.8, -35.8], [-27.1, 36], [-32.5, 36], [-32.5, 41.9], [-30.3, 43.8], [-29.4, 46.6], [-30.3, 49.9], [-32.6, 51.8], [-32.6, 57.9], [-25.9, 57.9], [-26, 63.9]]], levels: []},
  bxcourt: {anchor: [-73.9238, 40.8263], B: 24.5, foot: [[[-33.6, 37.8], [-10, 37.8], [-10, 42.1], [10.7, 42.1], [10.7, 37.9], [33.6, 37.9], [33.6, 10.4], [38.3, 10.4], [38.2, -10.5], [33.6, -10.5], [33.5, -37.5], [10.5, -37.5], [10.5, -42.3], [-10.6, -42.4], [-10.6, -37.5], [-33.7, -37.6], [-33.6, -9.9], [-38.2, -9.9], [-38.2, 10.4], [-33.6, 10.4]]], levels: []},
  armory: {anchor: [-73.8982, 40.8684], B: 26, foot: [[[-86.2, 56.4], [83.2, 43.3], [84.2, 56.3], [93.9, 55.6], [85.8, -45.8], [61, -43.9], [60.6, -46.3], [61.8, -49.2], [60.3, -52.1], [58.6, -52.8], [56.1, -52.3], [51.7, -53.2], [51.5, -54.7], [44.7, -56.8], [8.5, -54.2], [10.2, -57.1], [10, -60], [7.9, -62.6], [5.1, -63.5], [1.9, -62.5], [-0.1, -59.7], [0.1, -56.3], [2.2, -53.7], [-10.9, -52.7], [-8.7, -55], [-8.6, -58.9], [-10.7, -61.5], [-14, -62.3], [-17.1, -61], [-18.8, -58.2], [-18.4, -54.8], [-15.7, -52.3], [-53.3, -49.4], [-59.2, -47], [-58.7, -41.3], [-60.9, -41.1], [-61.7, -43.3], [-63.8, -44.5], [-65.7, -44.5], [-67.6, -43.2], [-68.3, -41.4], [-68.1, -39.5], [-66.6, -37.7], [-64.4, -37.2], [-64.3, -35.5], [-93.3, -33.3]]], levels: []},
  belvedere: {anchor: [-73.969, 40.7794], B: -36.7, foot: [[[8.4, 4.2], [4.5, 2.8], [5, 1.1], [4.5, -1.5], [2.3, -3.1], [3.6, -6.1], [6, -5.1], [9.5, -13], [6.8, -14.2], [8.9, -18.8], [5.2, -20.5], [5.3, -21.9], [2.6, -23], [1.8, -21.9], [2.4, -21.1], [-3.9, -8], [-8.8, -10.2], [-12.3, -2.4], [-7.1, -0.1], [-12.3, 11.4], [-4.7, 14.8], [-3.6, 12.4], [7.8, 17.6], [12.3, 7.8], [7.8, 5.8]]], levels: []},
  whitehall: {anchor: [-74.0131, 40.7011], B: -6.3, foot: [[[21.1, 54.3], [21.7, 56.7], [20.9, 58.7], [19.4, 60], [17.1, 61], [14.9, 60.9], [10.6, 58.1], [7.8, 61.9], [13.7, 65.4], [18.2, 65.6], [22.9, 63.5], [25.9, 59.5], [26.4, 57.5], [26.1, 51.1], [26.5, 46.7], [42.1, 3.4], [44.6, 3.8], [49.2, -22], [51.2, -21.6], [54.4, -39], [51, -22.5], [45, -23.4], [24.5, 34.9], [-18.6, 44.2], [-35.2, 21.9], [-38.6, 3.1], [-46.7, 28.4], [-46.4, 32], [-12, 68.7], [-8.8, 73.7], [-7.6, 78.7], [-8.2, 83.5], [-10.4, 87.7], [-40, 120], [-36.3, 123.4], [-6.4, 90.7], [-3.8, 85.7], [-2.8, 79], [-3.7, 73.4], [-6.8, 67.2], [-13.5, 60], [-14, 56.3], [-12.7, 53.4], [-9, 51.1], [11.6, 47.6], [14.9, 48.2], [17.8, 49.7]], [[12.8, -55.2], [56, -47.2], [54.6, -42.5], [50.7, -22.6], [44.8, -23.7], [24.4, 34.6], [-18.5, 43.9], [-34.9, 21.7], [-39.7, -3.5], [-39.6, -40.3], [-45.2, -40.3], [-45.2, -54.9], [-21.9, -55.4]], [[44.8, -23.7], [48.6, -43.6], [54.6, -42.5], [50.7, -22.6]], [[17.2, -35.7], [-11.8, -35.2], [-12, -48.9], [17, -49.4]], [[52.3, -30.6], [24.4, -35.5], [-39.6, -35.3], [-39.6, -40.3], [-45.2, -40.3], [-45.2, -54.9], [-21.9, -55.4], [12.8, -55.2], [52.8, -48], [56, -47.2]], [[-43.3, -46.3], [-43.5, -54.1], [9.5, -54.4], [17, -53.6], [56.1, -46.7], [54.2, -39.3], [15.3, -46.5]], [[-45.2, -51], [-39.5, -51], [-39.6, -40.3], [-45.2, -40.3]]], levels: []},
};
// </massing>

function toLocal(B: number, ring: V2[]): V2[] {
  const a = (-B * Math.PI) / 180;
  const c = Math.cos(a);
  const s = Math.sin(a);
  return ring.map(([u, v]) => [c * u - s * v, s * u + c * v] as V2);
}

/** Outline grown by about d metres (scaled about its centroid) for `replaces`. */
function grow(ring: V2[], d: number): V2[] {
  const cx = ring.reduce((a, p) => a + p[0], 0) / ring.length;
  const cy = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  const r = ring.reduce((a, p) => a + Math.hypot(p[0] - cx, p[1] - cy), 0) / ring.length;
  const k = 1 + d / r;
  return ring.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k] as V2);
}

function scaleV(ring: V2[], f: number, vc: number): V2[] {
  return ring.map(([u, v]) => [u, vc + (v - vc) * f] as V2);
}

type Spec = Omit<Landmark, 'anchor' | 'build' | 'replaces' | 'end'> & {
  m: Massing;
  end?: number;
  draw: (b: MeshBuilder, m: Massing) => void;
  pad?: number;
};

function lm(s: Spec): Landmark {
  const {m, draw, end, pad, ...rest} = s;
  return {
    ...rest,
    end: end ?? 9999,
    anchor: m.anchor,
    build: b => {
      b.frame(0, 0, 0, m.B, () => draw(b, m));
    },
    replaces: m.foot.map(r => toLocal(m.B, grow(r, pad ?? 1)))
  };
}

function stack(b: MeshBuilder, levels: Level[], zTop = Infinity) {
  for (const [z0, z1, ring] of levels) {
    if (z0 >= zTop) continue;
    b.prism(ring, z0, Math.min(z1, zTop), {bottom: z0 > 0});
  }
}

const WP = 'https://en.wikipedia.org/wiki/';
const OSM = 'https://www.openstreetmap.org/copyright';
const FOOT = 'https://data.cityofnewyork.us/City-Government/BUILDING/5zhs-2jue';
const CTBUH = 'https://www.skyscrapercenter.com/city/new-york-city';

// ---------------------------------------------------------------- One57
function drawOne57(b: MeshBuilder, m: Massing) {
  b.color('#6E8CA6');
  stack(b, m.levels, 306);
}

// ------------------------------------------------- Time Warner Center
function drawTWC(b: MeshBuilder, m: Massing) {
  b.color('#7E98AB');
  const lv = m.levels;
  // the curved base (mall, hotel, Jazz at Lincoln Center) and the two towers' stacks
  stack(b, lv, 230);
  // the two 55-storey towers end in 18 m lanterns (cited)
  b.color('#A9BAC5');
  b.prism(rect(11.7, -21, 22, 22), 230, 248, {});
  b.prism(rect(-21.8, 42.1, 22, 22), 230, 248, {});
}

// ------------------------------------------------------------ 53 West 53
function draw53(b: MeshBuilder, m: Massing) {
  const ring = m.foot[0];
  const vc = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  b.color('#8D8A84');
  b.prism(ring, 0, 30, {});
  // the diagrid tower: north and south faces lean in, east and west faces stay vertical
  const zs = [30, 90, 150, 210, 270, 320];
  const f = (z: number) => 1 - 0.4 * ((z - 30) / 290);
  b.loft(zs.map(z => scaleV(ring, f(z), vc)), zs, {top: true});
}

// --------------------------------------------------- 35 Hudson Yards
function draw35HY(b: MeshBuilder, m: Massing) {
  b.color('#8FA2AD');
  stack(b, m.levels, 300);
  b.color('#6A7A84');
  b.prism(rect(10, 0, 40, 22), 300, 308, {});
}

// -------------------------------------------------------- The Plaza
function drawPlaza(b: MeshBuilder, m: Massing) {
  b.color('#E4DAC6');
  b.prism(m.foot[0], 0, 58, {});
  b.color('#4E7D6C'); // green tiled mansard, three storeys
  stack(b, m.levels);
}

// -------------------------------------------------------- Carnegie Hall
function drawCarnegie(b: MeshBuilder, m: Massing, withTower: boolean) {
  b.color('#B07A5A');
  b.prism(m.foot[0], 0, 34, {});
  if (withTower) {
    b.color('#A66F52');
    b.prism(rect(-11.5, -19.2, 22.8, 23), 34, 55.2, {});
  }
}

// -------------------------------------------------------- The Dakota
function drawDakota(b: MeshBuilder, m: Massing) {
  const hole = m.levels[0][2];
  b.color('#B8A074');
  b.prism(m.foot[0], 0, 36, {holes: [hole]});
  b.color('#4C5459');
  for (const [z0, z1, ring, h] of DAKOTA_ROOF) b.prism(ring, z0, z1, {holes: [h], bottom: true});
}

// ---------------------------------------------------------- The Ansonia
function drawAnsonia(b: MeshBuilder, m: Massing) {
  b.color('#DCD0B8');
  b.prism(m.foot[0], 0, 61, {});
  b.color('#40504A');
  stack(b, m.levels);
  // corner cupolas
  for (const [x, y] of m.foot[0]) {
    const k = 0.9;
    const cx = x + (x > 0 ? -3.2 : 3.2) * k;
    const cy = y + (y > 0 ? -3.2 : 3.2) * k;
    b.color('#DCD0B8');
    b.cylinder(cx, cy, 3.3, 61, 78, 12);
    b.color('#40504A');
    b.dome(cx, cy, 3.5, 78, 7.3, 12, 4);
  }
}

function rect(cx: number, cy: number, sx: number, sy: number): V2[] {
  return [[cx - sx / 2, cy - sy / 2], [cx + sx / 2, cy - sy / 2], [cx + sx / 2, cy + sy / 2], [cx - sx / 2, cy + sy / 2]];
}

const DAKOTA_ROOF: [number, number, V2[], V2[]][] = [
  [36, 42, [[-29.8, 29.8], [28.8, 29.8], [28.7, -6.5], [27.6, -6.5], [27.6, -18.0], [28.6, -18.0], [28.6, -30.1], [-29.7, -30.1], [-29.6, -16.7], [-27.4, -16.7], [-27.3, 16.3], [-29.8, 16.3]], [[-8.7, 6.7], [-13.0, 6.7], [-15.0, 12.9], [-12.7, 16.0], [13.7, 16.0], [13.7, 6.6], [7.3, 6.6], [7.2, -6.7], [13.6, -6.7], [13.6, -17.0], [-14.3, -17.0], [-14.3, -7.3], [-8.8, -7.3]]],
  [42, 47, [[-28.3, 17.8], [-28.3, 28.3], [27.3, 28.3], [27.2, -5.0], [26.1, -5.0], [26.1, -19.5], [27.1, -19.5], [27.1, -28.6], [-28.2, -28.6], [-28.1, -18.2], [-25.9, -18.2], [-25.8, 17.8]], [[-10.2, 5.2], [-14.1, 5.2], [-16.6, 13.1], [-13.4, 17.5], [15.2, 17.5], [15.2, 5.1], [8.8, 5.1], [8.7, -5.2], [15.1, -5.2], [15.1, -18.5], [-15.8, -18.5], [-15.8, -5.8], [-10.3, -5.8]]],
  [47, 50.9, [[-26.8, 19.3], [-26.8, 26.8], [25.8, 26.8], [25.7, -3.5], [24.6, -3.5], [24.6, -21.0], [25.6, -21.0], [25.6, -27.1], [-26.7, -27.1], [-26.6, -19.7], [-24.4, -19.7], [-24.3, 19.3]], [[-11.7, 3.7], [-15.2, 3.7], [-18.3, 13.4], [-14.2, 19.0], [16.7, 19.0], [16.7, 3.6], [10.3, 3.6], [10.2, -3.7], [16.6, -3.7], [16.6, -20.0], [-17.3, -20.0], [-17.3, -4.3], [-11.8, -4.3]]]
];

const BASE: Landmark[] = [
  lm({
    id: 'one57',
    name: 'One57 (Carnegie 57)',
    kind: 'tower',
    built: [2009.3, 2014.62],
    m: M.one57,
    draw: drawOne57,
    facts: {
      Construction: '17 Apr 2009 – completed 13 Aug 2014',
      Height: '306 m (1,004 ft) to the roof',
      Floors: '73 above ground',
      Architects: 'Christian de Portzamparc; SLCE Architects (of record)',
      Model: 'plan from the city footprint; set-back levels from OpenStreetMap parts, capped at the cited roof; the curved cascade on 57th Street is drawn as steps; glazing colour estimated'
    },
    sources: [WP + 'One57', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'time_warner_center',
    name: 'Time Warner Center (Deutsche Bank Center)',
    kind: 'tower',
    built: [2000.85, 2004.1],
    m: M.twc,
    draw: drawTWC,
    facts: {
      Construction: '14 Nov 2000 – opened 5 Feb 2004',
      Height: '230 m (750 ft) to the roof, two towers with 18 m lanterns',
      Floors: '55 each',
      Architect: 'David Childs, Skidmore, Owings & Merrill',
      Model: 'curved base and tower plans from the city footprint and OpenStreetMap parts; the glass atrium and the Columbus Circle facade are not cut out; lantern size estimated'
    },
    sources: [WP + 'Deutsche_Bank_Center', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'w53',
    name: '53 West 53',
    kind: 'tower',
    built: [2014.9, 2020.12],
    m: M.w53,
    draw: draw53,
    facts: {
      Construction: 'late 2014 – completed Feb 2020',
      Height: '320 m (1,050 ft)',
      Floors: '77',
      Architects: 'Jean Nouvel; Adamson Associates (of record)',
      Model: 'plan from the city footprint; the 30 m base height and the lean (north and south faces taper to 60 % of the depth at the top) are estimated from photographs; diagrid and the five spires not drawn'
    },
    sources: [WP + '53_West_53', CTBUH, FOOT]
  }),
  lm({
    id: 'hudson_yards_35',
    name: '35 Hudson Yards',
    kind: 'tower',
    built: [2015.0, 2019.2],
    m: M.hy35,
    draw: draw35HY,
    facts: {
      Construction: '2015 – opened 15 Mar 2019',
      Height: '300 m (1,000 ft) to the roof; the city footprint measures 308 m with the rooftop mechanical',
      Floors: '72',
      Architect: 'David Childs, Skidmore, Owings & Merrill',
      Model: 'plan from the city footprint; three stepped levels from OpenStreetMap parts; the sloped faces and the Edge platform are not drawn; mechanical block estimated'
    },
    sources: [WP + '35_Hudson_Yards', CTBUH, FOOT, OSM]
  }),
  lm({
    id: 'plaza_hotel',
    name: 'The Plaza',
    kind: 'building',
    built: [1905.5, 1907.75],
    m: M.plaza,
    draw: drawPlaza,
    facts: {
      Construction: '1 Jul 1905 – opened 1 Oct 1907',
      Height: '76.8 m (252 ft) to the roof; the footprint file measures 85 m with the turrets',
      Floors: '18',
      Architect: 'Henry J. Hardenbergh',
      Model: 'plan from the city footprint; cornice at 58 m and the three-storey mansard stepped in, both estimated; turrets and dormers not drawn'
    },
    sources: [WP + 'The_Plaza_Hotel', 'https://s-media.nyc.gov/agencies/lpc/lp/0868.pdf', FOOT]
  }),
  lm({
    id: 'carnegie_hall_1891',
    name: 'Carnegie Hall (as opened, 1891–1894)',
    kind: 'building',
    built: [1889.4, 1891.35],
    end: 1894.5,
    m: M.carnegie,
    draw: (b, m) => drawCarnegie(b, m, false),
    facts: {
      Construction: 'excavation 1889, cornerstone 13 May 1890 – opened 5 May 1891',
      Height: 'eight storeys (about 34 m, estimated)',
      Architect: 'William B. Tuthill',
      Model: 'plan from the city footprint; one block, height estimated from eight storeys'
    },
    sources: [WP + 'Carnegie_Hall', FOOT]
  }),
  lm({
    id: 'carnegie_hall',
    name: 'Carnegie Hall',
    kind: 'building',
    built: [1894.0, 1896.5],
    m: M.carnegie,
    draw: (b, m) => drawCarnegie(b, m, true),
    facts: {
      Construction: 'hall 1889–91; studio tower at Seventh Avenue and 56th Street 1894–96',
      Height: '55 m (the city footprint) at the studio tower',
      Floors: '13 at the tower, 8 at the hall',
      Architect: 'William B. Tuthill',
      Model: 'plan and tower height from the city footprint; the position and plan of the tower on the south-west corner and the hall block height are estimated'
    },
    sources: [WP + 'Carnegie_Hall', 'https://s-media.nyc.gov/agencies/lpc/lp/0264.pdf', FOOT]
  }),
  lm({
    id: 'dakota',
    name: 'The Dakota',
    kind: 'building',
    built: [1880.8, 1884.8],
    m: M.dakota,
    draw: drawDakota,
    facts: {
      Construction: 'Oct 1880 – Oct 1884',
      Height: '56 m (185 ft) with finials; the model ends at the footprint file’s 50.9 m roof',
      Floors: '7 with gables and garrets',
      Architect: 'Henry J. Hardenbergh',
      Model: 'outline and courtyard from the city footprint; wall height (36 m) and the stepped roof are estimated; gables, turrets and dormers not drawn'
    },
    sources: [WP + 'The_Dakota', 'https://s-media.nyc.gov/agencies/lpc/lp/0071.pdf', FOOT]
  }),
  lm({
    id: 'ansonia',
    name: 'The Ansonia',
    kind: 'building',
    built: [1899.87, 1904.3],
    m: M.ansonia,
    draw: drawAnsonia,
    facts: {
      Construction: '15 Nov 1899 – hotel dedicated Apr 1904',
      Height: '85 m (the city footprint’s roof, with the cupolas)',
      Floors: '17',
      Architect: 'Paul E. Duboy',
      Model: 'plan and roof height from the city footprint; wall/mansard split and the four corner cupolas are estimated; the light courts and the rounded corner towers are not drawn'
    },
    sources: [WP + 'Ansonia_(Manhattan)', 'https://s-media.nyc.gov/agencies/lpc/lp/0951.pdf', FOOT]
  })
];

// ======================================================= second round (same file)
function scl(ring: V2[], fu: number, fv: number): V2[] {
  const cu = ring.reduce((a, p) => a + p[0], 0) / ring.length;
  const cv = ring.reduce((a, p) => a + p[1], 0) / ring.length;
  return ring.map(([u, v]) => [cu + (u - cu) * fu, cv + (v - cv) * fv] as V2);
}
function ell(cx: number, cy: number, rx: number, ry: number, n = 24): V2[] {
  return Array.from({length: n}, (_, i) => [cx + rx * Math.cos((i / n) * 2 * Math.PI), cy + ry * Math.sin((i / n) * 2 * Math.PI)] as V2);
}

function drawOculus(b: MeshBuilder, m: Massing) {
  b.color('#ECEBE6');
  b.prism(m.foot[0], 0, 8, {});
  b.loft([m.foot[0], scl(m.foot[0], 0.9, 0.6), scl(m.foot[0], 0.88, 0.1)], [8, 22, 33.03], {top: true});
}
function drawJavits(b: MeshBuilder, m: Massing) {
  b.color('#8FB0BC'); // glass curtain wall on a space frame
  b.prism(m.foot[0], 0, 53.57, {});
}
function drawJavitsX(b: MeshBuilder, m: Massing) {
  b.color('#86A7B4');
  b.prism(m.foot[0], 0, 53.57, {});
}
function drawWhitney(b: MeshBuilder, m: Massing) {
  b.color('#9AA2A6');
  b.prism(m.foot[0], 0, 10.5, {});
  b.prism(rect(-24, -6, 34, 21), 10.5, 38, {});
  b.prism(rect(3, -6, 20, 21), 10.5, 27, {});
}
function drawCloisters(b: MeshBuilder, m: Massing) {
  b.color('#C9BBA0');
  b.prism(m.foot[0], 0, 14, {});
  b.prism(rect(0.5, 44.0, 9, 9), 14, 33.45, {});
  b.color('#6F6A60');
  b.pyramid(rect(0.5, 44.0, 9.4, 9.4), 33.45, [0.5, 44.0, 38]);
}
function drawTWA(b: MeshBuilder, m: Massing) {
  b.color('#D8D6D0');
  b.prism(m.foot[0], 0, 7.32, {});
  b.loft([ell(0, 0, 30, 42), ell(0, 0, 26, 36), ell(0, 0, 20, 27)], [16, 20, 23], {top: true});
  for (const [x, y] of [[-22, -14], [22, -14], [-22, 14], [22, 14]]) b.prism(rect(x, y, 3, 3), 7.32, 16, {});
}
function drawWhitehall(b: MeshBuilder, m: Massing) {
  b.color('#A9B4BA');
  const hs = [27.74, 15, 24, 24, 20, 23, 24];
  m.foot.forEach((r, i) => b.prism(r, 0, hs[i], {}));
}
function drawApollo(b: MeshBuilder, m: Massing) {
  b.color('#E7E1D2'); // white glazed terracotta
  b.prism(m.foot[0], 0, 20.05, {});
}
function drawSanRemo(b: MeshBuilder, m: Massing) {
  b.color('#D9CFB8');
  b.prism(m.foot[0], 0, 75.9, {});
  for (const y of [-23, 24]) {
    b.prism(rect(12, y, 13, 13), 75.9, 105, {});
    b.cylinder(12, y, 4.6, 105, 114, 16);
    b.color('#8AA392');
    b.dome(12, y, 3.6, 114, 6.5, 12, 4);
    b.color('#D9CFB8');
  }
}
function drawBelvedere(b: MeshBuilder, m: Massing) {
  b.color('#8A8478'); // Manhattan schist and granite
  b.prism(m.foot[0], 0, 7.62, {});
  b.cylinder(0, 0, 2.5, 7.62, 15, 12);
  b.color('#5E5A55');
  b.frustum(0, 0, 3, 0.3, 15, 19, 12);
}
function drawQueensBldg(b: MeshBuilder, m: Massing) {
  b.color('#CFC9BC');
  b.prism(m.foot[0], 0, 15.3, {});
}
function drawBPL(b: MeshBuilder, m: Massing) {
  b.color('#D8D2C0'); // Indiana limestone
  b.prism(m.foot[0], 0, 24, {});
}
function drawBxCourt(b: MeshBuilder, m: Massing) {
  b.color('#D3CDBE');
  b.prism(m.foot[0], 0, 58.49, {});
}
function drawArmory(b: MeshBuilder, m: Massing) {
  b.color('#A98A6E');
  b.prism(m.foot[0], 0, 30.5, {});
  for (const [x, y] of [[-87.7, -31.3], [80.5, -43.0], [88.7, 52.5], [-81.2, 53.1]]) b.prism(rect(x, y, 9, 9), 30.5, 39.37, {});
}

const NEW: Landmark[] = [
  lm({
    id: 'oculus', name: 'Oculus (World Trade Center Transportation Hub)', kind: 'building', built: [2008.5, 2016.17], m: M.oculus, draw: drawOculus,
    facts: {Construction: 'ribs from 8 Jul 2008 – partly opened 3 Mar 2016', Height: '33 m (the footprint file’s measured roof)', Architect: 'Santiago Calatrava',
      Model: 'plan and roof height from the city footprint; the ribbed wings are drawn as a three-step taper (shape estimated); 114 ribs and the skylight not drawn'},
    sources: [WP + 'World_Trade_Center_Transportation_Hub', FOOT]
  }),
  lm({
    id: 'javits', name: 'Jacob K. Javits Convention Center', kind: 'building', built: [1980.46, 1986.25], m: M.javits, draw: drawJavits,
    facts: {Construction: 'groundbreaking 18 Jun 1980 – opened 3 Apr 1986', Height: '53.6 m (the footprint file’s measured maximum, applied to the whole block)', Architect: 'James Ingo Freed, Pei Cobb Freed & Partners',
      Model: 'the 1986 plan is the 2023 footprint without its north strip; the height is the single measured maximum, so the halls are drawn too tall; space frame not drawn'},
    sources: [WP + 'Jacob_K._Javits_Convention_Center', FOOT]
  }),
  lm({
    id: 'javits_expansion', name: 'Javits Center expansion (north strip)', kind: 'building', built: [2018.0, 2021.36], m: M.javits_x, draw: drawJavitsX,
    facts: {Construction: 'expansion completed 11 May 2021 (start year estimated)', Height: '53.6 m (measured maximum)', Architect: 'FXFOWLE (renovation and expansion)',
      Model: 'the strip of the 2023 footprint north of the 1986 plan, taken as the expansion; its extent and start are estimated'},
    sources: [WP + 'Jacob_K._Javits_Convention_Center', FOOT]
  }),
  lm({
    id: 'whitney_gansevoort', name: 'Whitney Museum of American Art (Gansevoort Street)', kind: 'building', built: [2010.0, 2015.33], m: M.whitney, draw: drawWhitney,
    facts: {Construction: '2010 – opened 1 May 2015', Floors: '8', Architect: 'Renzo Piano',
      Model: 'plan from the city footprint (its measured roof is 10.5 m, the low part); the tall western block (38 m, eight storeys) and the terraced middle block (27 m) are estimates; no cited height'},
    sources: [WP + 'Whitney_Museum_of_American_Art', FOOT]
  }),
  lm({
    id: 'cloisters', name: 'The Cloisters', kind: 'building', built: [1934.5, 1938.36], m: M.cloisters, draw: drawCloisters,
    facts: {Construction: '1934/35 – opened 10 May 1938', Floors: '2 levels on the hillside', Architect: 'Charles Collens',
      Model: 'plan and the 33.5 m height from the city footprint; the 14 m body and the position of the tower (north-east end) are estimated'},
    sources: [WP + 'The_Cloisters', FOOT]
  }),
  lm({
    id: 'twa_flight_center', name: 'TWA Flight Center', kind: 'building', built: [1959.44, 1962.41], m: M.twa, draw: drawTWA,
    facts: {Construction: '9 Jun 1959 – dedicated 28 May 1962', Height: '23 m (75 ft) at the shells; Y piers 16 m', Architect: 'Eero Saarinen',
      Model: 'plan from the city footprint of the terminal complex; the shell is an ellipse, its position and size and the pier positions are estimated; the flight tubes are inside the footprint but not drawn'},
    sources: [WP + 'TWA_Flight_Center', FOOT]
  }),
  lm({
    id: 'whitehall_terminal', name: 'Staten Island Ferry — Whitehall Terminal', kind: 'building', built: [2003.0, 2005.1], m: M.whitehall, draw: drawWhitehall,
    facts: {Construction: 'start estimated 2003 – opened 8 Feb 2005', Floors: '4', Architect: 'Anderson/Schwartz Architects (Frederic Schwartz)',
      Model: 'seven parts of the city footprint at their measured roof heights (15–28 m); the curtain wall and the slips are not drawn'},
    sources: [WP + 'Whitehall_Terminal', FOOT]
  }),
  lm({
    id: 'apollo_theater', name: 'Apollo Theater', kind: 'building', built: [1913.0, 1914.1], m: M.apollo, draw: drawApollo,
    facts: {Construction: '1913 – 1914', Floors: '3 on the facade', Architect: 'George Keister',
      Model: 'plan and 20 m height from the city footprint (measured roof); no marquee'},
    sources: [WP + 'Apollo_Theater', FOOT]
  }),
  lm({
    id: 'san_remo', name: 'The San Remo', kind: 'tower', built: [1929.0, 1930.72], m: M.sanremo, draw: drawSanRemo,
    facts: {Construction: '1929 – 21 Sep 1930', Height: '120 m (400 ft)', Floors: '27 (17 in the base, 10 more in each tower)', Architect: 'Emery Roth',
      Model: 'plan from the city footprint (courtyard not cut out); total height 120.5 m is the footprint’s and the cited 120 m; base 75.9 m (17/27 of the height) and the tower plans (13 m squares) are estimated; temples drawn as colonnade and dome'},
    sources: [WP + 'The_San_Remo', 'https://s-media.nyc.gov/agencies/lpc/lp/1049.pdf', FOOT]
  }),
  lm({
    id: 'belvedere_castle', name: 'Belvedere Castle', kind: 'building', built: [1867.0, 1869.9], m: M.belvedere, draw: drawBelvedere,
    facts: {Construction: '1867 – 1869', Architects: 'Calvert Vaux and Jacob Wrey Mould',
      Model: 'plan and 7.6 m body from the city footprint; the tower’s position, its 15 m height and the conical cap are estimated; no cited height'},
    sources: [WP + 'Belvedere_Castle', FOOT]
  }),
  lm({
    id: 'queens_museum', name: 'Queens Museum (New York City Building)', kind: 'building', built: [1937.6, 1939.33], m: M.queens, draw: drawQueensBldg,
    facts: {Construction: '1937 – dedicated 30 Apr 1939', Height: '15.3 m (measured; the ceiling is about 12 m)', Architect: 'Aymar Embury II',
      Model: 'plan from the 2023 footprint, which includes the museum’s 2013 expansion on the south; the 1939 plan was 110 by 37 m; flat box'},
    sources: [WP + 'Queens_Museum', FOOT]
  }),
  lm({
    id: 'brooklyn_central_library', name: 'Brooklyn Public Library — Central Library', kind: 'building', built: [1938.0, 1941.24], m: M.bpl, draw: drawBPL,
    facts: {Construction: 'resumed 1938 (first begun 1912) – dedicated 29 Mar 1941', Height: '24 m (80 ft) at the entrance facade', Floors: '3–4', Architects: 'Githens and Keally',
      Model: 'plan from the city footprint; whole building drawn at the cited facade roof (the footprint’s highest part, 29 m, is not drawn); gilded entrance not drawn'},
    sources: [WP + 'Central_Library_(Brooklyn_Public_Library)', FOOT]
  }),
  lm({
    id: 'bronx_county_courthouse', name: 'Bronx County Courthouse', kind: 'building', built: [1931.0, 1934.9], m: M.bxcourt, draw: drawBxCourt,
    facts: {Construction: '1931 – 1934', Height: '58.5 m (measured roof)', Floors: '9', Architects: 'Joseph H. Freedlander and Max Hausle',
      Model: 'plan and height from the city footprint; the interior court and set-backs are not drawn'},
    sources: [WP + 'Bronx_County_Courthouse', FOOT]
  }),
  lm({
    id: 'kingsbridge_armory', name: 'Kingsbridge Armory (Eighth Coastal Artillery Armory)', kind: 'building', built: [1912.0, 1917.5], m: M.armory, draw: drawArmory,
    facts: {Construction: 'authorised 1911, begun about 1912 – 1917 (dates not given exactly)', Height: '39.4 m (measured maximum); the drill-hall truss is 30 m', Architects: 'Pilcher & Tachau',
      Model: 'plan from the city footprint; drill hall at the cited 30 m truss height, four corner turrets of 9 m squares at 39.4 m, their count and positions estimated'},
    sources: [WP + 'Kingsbridge_Armory', FOOT]
  })
];

export const MORE_B: Landmark[] = [...BASE, ...NEW];
