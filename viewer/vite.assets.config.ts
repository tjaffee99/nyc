// The page and its scripts only, without copying public/ (the data): for shipping a viewer change on
// top of data that is already built and published (pipeline rebuilds rewrite public/ for hours).
import {defineConfig, mergeConfig} from 'vite';
import base from './vite.config';

export default mergeConfig(base, defineConfig({publicDir: false}));
