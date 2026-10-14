// MemeCapes launchpad: the page never opens a websocket; confirmations are polled over HTTP.
class Emitter { constructor(){this._h={}} on(e,f){(this._h[e]=this._h[e]||[]).push(f);return this} once(e,f){return this.on(e,f)} off(){return this} removeListener(){return this} removeAllListeners(){return this} emit(e,...a){(this._h[e]||[]).forEach(f=>{try{f(...a)}catch(_){}});return true} }
export class CommonClient extends Emitter {
  constructor(){super()}
  connect(){} close(){}
  call(m){return Promise.reject(new Error('websocket calls are off in this build ('+m+')'))}
  notify(){return Promise.resolve()}
  subscribe(){return Promise.resolve()} unsubscribe(){return Promise.resolve()}
}
export function WebSocket(){return {readyState:3,close(){},send(){},addEventListener(){},removeEventListener(){}}}
export default {CommonClient, WebSocket};
