// Builds lp/lpcore.js: Solana web3.js + Anchor + Meteora's Dynamic Bonding Curve SDK in one browser file,
// from source checkouts (tools/launchpad/vendor.sh clones them at fixed versions into $LP_VENDOR).
// Run from the repo root:  node tools/launchpad/build.mjs
import { createRequire } from 'module';
import path from 'path';
import fs from 'fs';
const require = createRequire(import.meta.url);
const esbuild = require(process.env.ESBUILD || '/opt/npm-tools/node_modules/esbuild');

const V = process.env.LP_VENDOR || '/home/claude/scratch/lp/vendor';
const SH = path.resolve('tools/launchpad/shims');
const SDK = `${V}/dbc-sdk/packages/dynamic-bonding-curve/src`;

// package name -> file (exact) ; prefix packages map subpaths into a source folder
const exact = {
  '@solana/web3.js': `${V}/web3/src/index.ts`,
  '@coral-xyz/anchor': `${V}/anchor/ts/packages/anchor/src/index.ts`,
  '@coral-xyz/anchor-errors': `${V}/anchor/ts/packages/anchor-errors/src/index.ts`,
  '@coral-xyz/borsh': `${V}/anchor/ts/packages/borsh/src/index.ts`,
  '@meteora-ag/dynamic-bonding-curve-sdk': `${SDK}/index.ts`,
  '@solana/spl-token': `${SH}/spl-token.js`,
  '@solana/buffer-layout': `${V}/solana-buffer-layout/src/Layout.ts`,
  '@solana/codecs-numbers': `${V}/kit/packages/codecs-numbers/src/index.ts`,
  '@solana/codecs-core': `${V}/kit/packages/codecs-core/src/index.ts`,
  '@solana/errors': `${V}/kit/packages/errors/src/index.ts`,
  'bn.js': `${V}/bn.js/lib/bn.js`,
  'decimal.js': `${V}/decimal.js/decimal.mjs`,
  'buffer': `${V}/buffer/index.js`,
  'base64-js': `${V}/base64-js/index.js`,
  'ieee754': `${V}/ieee754/index.js`,
  'bs58': `${V}/bs58/index.js`,
  'base-x': `${V}/base-x/src/index.js`,
  'safe-buffer': `${V}/safe-buffer/index.js`,
  'borsh': `${V}/borsh/lib/index.js`,
  'uuid': `${SH}/uuid.js`, 'util': `${SH}/util.js`, 'process': `${SH}/process.js`,
  'fast-stable-stringify': `${V}/fast-stable-stringify/index.js`,
  'jayson/lib/client/browser': `${V}/jayson/lib/client/browser/index.js`,
  'jayson': `${SH}/jayson.js`,
  'rpc-websockets': `${SH}/rpc-websockets.js`,
  'node-fetch': `${SH}/cross-fetch.js`,
  'cross-fetch': `${SH}/cross-fetch.js`,
  'text-encoding-utf-8': `${SH}/text-encoding-utf-8.js`,
  'agentkeepalive': `${SH}/empty.js`,
  'http': `${SH}/empty.js`, 'https': `${SH}/empty.js`, 'fs': `${SH}/empty.js`, 'path': `${SH}/empty.js`, 'os': `${SH}/empty.js`,
  'crypto': `${SH}/empty.js`, 'toml': `${SH}/empty.js`, 'pako': `${SH}/pako.js`,
  'buffer-layout': `${V}/buffer-layout/lib/Layout.js`,
  'camelcase': `${V}/camelcase/index.js`,
  'eventemitter3': `${V}/eventemitter3/index.js`,
};
const prefix = {
  '@noble/curves/': `${V}/noble-curves/src/`,
  '@noble/hashes/': `${V}/noble-hashes/src/`,
};
// superstruct: web3.js wants v2, anchor wants v0.15
const superstructFor = (importer) => importer.includes('/anchor/') ? `${V}/superstruct015/src/index.ts` : `${V}/superstruct2/src/index.ts`;

function tsOrJs(p) {
  const base = p.replace(/\.js$/, '');
  for (const c of [p, base + '.ts', base + '.js', base + '/index.ts', base + '/index.js']) if (fs.existsSync(c) && fs.statSync(c).isFile()) return c;
  return null;
}

const resolver = {
  name: 'lp-resolve',
  setup(b) {
    b.onResolve({ filter: /^[^./]/ }, (a) => {
      if (a.path === 'superstruct') return { path: superstructFor(a.importer) };
      if (exact[a.path]) return { path: exact[a.path] };
      for (const k in prefix) if (a.path.startsWith(k)) {
        const f = tsOrJs(prefix[k] + a.path.slice(k.length));
        if (f) return { path: f };
      }
      if (a.path === '@noble/curves') return { path: `${V}/noble-curves/src/index.ts` };
      if (a.path === '@noble/hashes') return { path: `${V}/noble-hashes/src/index.ts` };
      return { errors: [{ text: 'not vendored: ' + a.path + ' (from ' + a.importer + ')' }] };
    });
    // web3.js browser build swaps fetch-impl for its browser fork
    b.onResolve({ filter: /fetch-impl$/ }, (a) => a.importer.includes('/web3/src/') ? { path: `${V}/web3/src/__forks__/browser/fetch-impl.ts` } : undefined);
    // relative imports inside the vendored sources: allow ".js" specifiers that point at ".ts" files
    b.onResolve({ filter: /^\.\.?\// }, (a) => {
      const f = tsOrJs(path.resolve(a.resolveDir, a.path));
      return f ? { path: f } : undefined;
    });
  },
};

const out = process.argv[2] || 'lp/lpcore.js';
fs.mkdirSync(path.dirname(out), { recursive: true });
const r = await esbuild.build({
  entryPoints: [path.resolve('tools/launchpad/entry.js')],
  bundle: true, format: 'iife', globalName: 'LPCORE', platform: 'browser', target: ['es2020'],
  minify: !process.env.NOMIN, sourcemap: false, legalComments: 'eof', outfile: out,
  define: { 'process.env.BROWSER': 'true', 'process.env.NODE_ENV': '"production"', 'global': 'globalThis', '__DEV__': 'false' },
  inject: [path.resolve('tools/launchpad/shims/inject.js')],
  plugins: [resolver], logLevel: 'warning', metafile: true,
});
const size = fs.statSync(out).size;
console.log('built', out, (size / 1024).toFixed(0) + ' KB');
