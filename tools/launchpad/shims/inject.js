// globals some vendored CommonJS code expects in a browser
import { Buffer } from 'buffer';
export { Buffer };
export const process = (typeof globalThis.process !== 'undefined') ? globalThis.process : { env: { BROWSER: true }, browser: true, version: '', versions: {}, nextTick: (f, ...a) => Promise.resolve().then(() => f(...a)) };
