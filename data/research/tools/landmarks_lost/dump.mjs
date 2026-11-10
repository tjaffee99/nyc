import {createRequire} from 'module';
const require = createRequire('/home/user/nyc/viewer/package.json');
const esbuild = require('esbuild');
const out = '/home/user/nyc/data/interim/landmarks_lost/dump_bundle.cjs';
await esbuild.build({entryPoints: ['/home/user/nyc/data/interim/landmarks_lost/dump_entry.ts'], bundle: true, platform: 'node', format: 'cjs', outfile: out, nodePaths: ['/home/user/nyc/viewer/node_modules'], logLevel: 'error'});
require(out);
