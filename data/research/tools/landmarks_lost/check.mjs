import {createRequire} from 'module';
const require = createRequire('/home/user/nyc/viewer/package.json');
const esbuild = require('esbuild');
const out = '/home/user/nyc/data/interim/landmarks_lost/check_bundle.cjs';
await esbuild.build({entryPoints: ['/home/user/nyc/data/interim/landmarks_lost/check_entry.ts'], bundle: true, platform: 'node', format: 'cjs', outfile: out, nodePaths: ['/home/user/nyc/viewer/node_modules'], logLevel: 'error'});
process.argv.splice(2, 0);
require(out);
