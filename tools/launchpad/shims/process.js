const p = (typeof globalThis.process !== 'undefined') ? globalThis.process : { env: {}, browser: true, cwd: () => '/', version: '', versions: {} }; export default p; export const env = p.env;
