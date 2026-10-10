#!/usr/bin/env python3
"""The MemeCapes look for every in-game screen: crimson velvet, gold leaf, ink stamps and a wax seal.

- Every modal (shops, bank, quests, capes, Telly, market, trade) gets the velvet-and-gold ledger look.
- Titles use Cinzel like the website; body text uses Alegreya (Georgia if the font is still loading).
- The Stock Market and trade screens have their own pieces: the ticker tape, offer tickets with BUY/SELL
  stamps, price sparklines, the two vaults and the wax seal.
Run from the repo root after patch_market.py:  python3 tools/patch_theme.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# the website's fonts
rep('<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&display=swap" rel="stylesheet">',
    '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Alegreya:wght@400;700&display=swap" rel="stylesheet">')

CSS = r"""
/* ---- the MemeCapes ledger: crimson velvet, gold leaf */
#modal{background:#0d0407d0}
#mb{max-width:400px;background:radial-gradient(120% 70% at 50% 0%,#5a1220 0%,#3b0b14 48%,#24060c 100%);border:3px solid #15030a;outline:2px solid #d9a520;box-shadow:0 0 0 5px #24060c,0 0 0 6px #6b4a06,0 24px 60px #000d;color:#f6eedc;font:13px/1.45 Alegreya,Georgia,serif;padding:14px;border-radius:3px;scrollbar-width:thin;scrollbar-color:#d9a520 #24060c}
#mb h2,#sbox h2{font:900 19px/1.15 Cinzel,Georgia,serif;letter-spacing:.4px;margin:0 0 10px;padding-bottom:7px;position:relative;border-bottom:1px solid #d9a52044;background:linear-gradient(#fff2a8,#f2b400 55%,#c98a10);-webkit-background-clip:text;background-clip:text;color:transparent}
#mb h2::after,#sbox h2::after{content:"";position:absolute;left:0;bottom:-1px;width:58px;height:2px;background:#ffd23f}
#mb h3{font:700 14px Cinzel,Georgia,serif;color:#ffd23f;margin:8px 0 6px}
#mb .row{border-bottom:1px solid #ffd23f22;padding:5px 0}
#mb small{color:#d9b98a}
#mb p{margin:4px 0 8px}
#mb button,#panel button,#sbox button:not(.big),#wm button{font:700 12px/1 Cinzel,Georgia,serif;letter-spacing:.3px;color:#ffe9b0;background:linear-gradient(#7a1420,#4a0a12);border:1px solid #d9a520aa;box-shadow:inset 0 1px 0 #ffffff1f,0 2px 0 #15030a;padding:7px 11px;border-radius:3px;cursor:pointer;text-shadow:0 1px 0 #000;transition:filter .12s,transform .08s}
#mb button:hover,#panel button:hover,#sbox button:hover,#wm button:hover{filter:brightness(1.18)}#mb button:active,#panel button:active,#sbox button:not(.big):active,#wm button:active{transform:translateY(1px);box-shadow:inset 0 1px 0 #ffffff1f,0 1px 0 #15030a}
#mb button:focus-visible,#panel button:focus-visible,#sbox button:focus-visible,#wm button:focus-visible{outline:2px solid #ffd23f;outline-offset:2px}
#mb button:disabled,#panel button:disabled{opacity:.45;cursor:default;filter:none}
#mb button.gold,#mb button[data-mkgo],#mb button[data-tacc],#mb button[data-mkc],#mb button[data-buy],#mb button[data-cp],#mb button[data-qc],#mb button[data-mc]{color:#2a1400;background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);border-color:#6b4a06;text-shadow:0 1px 0 #fff7}
#mb button.ghost{background:none;border-color:transparent;box-shadow:none;color:#d9b98a;text-decoration:underline;text-underline-offset:3px}
#mb input,#sbox input:not([type=checkbox]):not([type=radio]),#sbox select{background:#1a0408;border:1px solid #d9a52088;color:#f6eedc;font:13px Alegreya,Georgia,serif;padding:6px 8px;border-radius:3px;outline:0;user-select:text;-webkit-user-select:text}
#mb input:focus,#sbox input:focus{border-color:#ffd23f;box-shadow:0 0 0 2px #ffd23f33}
#mb .s{background:#1a0408;border:1px solid #d9a52033;border-radius:3px}
#mb .s svg{filter:drop-shadow(0 1px 1px #000)}
/* ---- the Stock Market */
#mb.mk{max-width:600px}#mb.tr{max-width:620px}
.mk-head{display:flex;align-items:center;gap:10px;margin:-14px -14px 0;padding:10px 14px;background:linear-gradient(#15030a,#2b0810);border-bottom:1px solid #d9a52066}
.mk-head h2{margin:0;padding:0;border:0;flex:1}.mk-head h2::after{display:none}.mk-head small{font:12px Alegreya,Georgia,serif;color:#d9b98a}
.mk-logo{width:36px;height:36px;border-radius:50%;box-shadow:0 0 0 2px #d9a520,0 0 14px #ffd23f55;flex:none}
.mk-tape{margin:0 -14px;background:#12030600;background:#120306;border-bottom:1px solid #d9a52044;overflow:hidden;white-space:nowrap;font:700 11px Cinzel,Georgia,serif;color:#d9b98a;position:relative}
.mk-tape::before,.mk-tape::after{content:"";position:absolute;top:0;bottom:0;width:30px;z-index:1;pointer-events:none}
.mk-tape::before{left:0;background:linear-gradient(90deg,#120306,#12030600)}.mk-tape::after{right:0;background:linear-gradient(270deg,#120306,#12030600)}
.mk-track{display:inline-flex;animation:mk-tick var(--dur,60s) linear infinite;will-change:transform}
.mk-tape:hover .mk-track{animation-play-state:paused}
.mk-track span{display:inline-flex;align-items:center;gap:5px;padding:6px 14px;border-right:1px solid #d9a52022}
.mk-track svg{width:16px;height:16px;margin:0}.mk-track b{color:#f6eedc}.mk-track i{font-style:normal;font-size:12px;color:#8a6a3a;line-height:1}.mk-track i.up{color:#39ff88}.mk-track i.dn{color:#ff7a59}
@keyframes mk-tick{to{transform:translateX(-50%)}}
@media (prefers-reduced-motion:reduce){.mk-track{animation:none}}
.mk-tabs{display:flex;gap:6px;margin:12px 0 10px;align-items:flex-end}
#mb .mk-tabs button{background:#1a0408;color:#d9b98a;border:1px solid #d9a52055;border-bottom-color:transparent;border-radius:4px 4px 0 0;padding:7px 12px;box-shadow:none}
#mb .mk-tabs button.on{background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);color:#2a1400;border-color:#6b4a06;text-shadow:0 1px 0 #fff7}
.mk-tabs .sp{flex:1;align-self:stretch;border-bottom:1px solid #d9a52055}
#mb .mk-tabs .pt{margin-left:auto;border-bottom-color:#d9a52055;border-radius:4px}
.mk-note{color:#d9b98a;font-size:12px;margin:0 0 8px}
.mk-tickets{display:grid;grid-template-columns:1fr;gap:6px}
@media (min-width:560px){.mk-tickets{grid-template-columns:1fr 1fr}}
.tk{position:relative;border:1px solid #d9a52066;border-radius:4px;padding:8px 10px;background:linear-gradient(#2b0810,#1f0509);min-height:74px;display:flex;flex-direction:column;gap:5px;box-sizing:border-box}
.tk.empty{border-style:dashed;justify-content:space-between;align-items:center;flex-direction:row;gap:8px;color:#b89a6a;background:#1a040866}
.tk.empty span{font-size:12px}
.tk.ready{border-color:#ffd23f;box-shadow:inset 0 0 0 1px #ffd23f44,0 0 14px #ffd23f33}
.tk-top{display:flex;align-items:center;gap:8px}
.tk-ico{width:34px;height:34px;border-radius:50%;background:radial-gradient(#5a1220,#24060c);box-shadow:0 0 0 1px #d9a520aa;display:grid;place-items:center;flex:none}
.tk-ico svg{width:26px;height:26px;margin:0}
.tk-name{flex:1;min-width:0}.tk-name b{display:block;font:700 13px Cinzel,Georgia,serif;color:#ffe9b0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tk-name small{color:#d9b98a;display:block}
.stamp{font:900 11px Cinzel,Georgia,serif;letter-spacing:2px;padding:3px 7px 2px;border:2px solid currentColor;border-radius:3px;transform:rotate(-7deg);opacity:.92;flex:none;line-height:1}
.stamp.buy{color:#39ff88}.stamp.sell{color:#ff7a59}.stamp.done{color:#ffd23f}
.tk-bar{height:7px;background:#120306;border:1px solid #000;border-radius:4px;overflow:hidden}
.tk-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#c98a10,#ffd23f);box-shadow:0 0 8px #ffd23f88;transition:width .4s}
.tk-bar.buy i{background:linear-gradient(90deg,#1e9a52,#39ff88);box-shadow:0 0 8px #39ff8866}.tk-bar.sell i{background:linear-gradient(90deg,#b3121f,#ff7a59);box-shadow:0 0 8px #ff7a5966}
.tk-foot{display:flex;justify-content:space-between;align-items:center;gap:6px;font-size:12px;color:#d9b98a;margin-top:auto}
.tk-foot b{color:#f6eedc}#mb .tk-foot button{padding:5px 9px;font-size:11px}#mb .tk-foot .ghost{padding:5px 4px}
.mk-form{border:1px solid #d9a52066;border-radius:4px;padding:10px 12px;background:#1f0509}
.mk-form .row{align-items:center;gap:8px}
.qbtn{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
#mb .qbtn button{padding:5px 8px;font-size:11px;min-width:34px}
.mk-total{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin:10px 0 10px;padding-top:8px;border-top:1px solid #d9a52033;flex-wrap:wrap}
.mk-total b{font:900 20px Cinzel,Georgia,serif;color:#ffd23f}
.mk-list{max-height:250px;overflow:auto;border:1px solid #d9a52033;border-radius:4px;padding:0 8px;background:#1a0408;margin-top:6px}
.mk-list .row:last-child{border-bottom:0}
#mb #geq{width:100%;box-sizing:border-box}
.pr{display:grid;grid-template-columns:30px 1fr 64px 80px;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #ffd23f22}
.pr:last-child{border-bottom:0}.pr svg.ic{width:26px;height:26px;margin:0}.pr svg.sp{width:64px;height:18px;overflow:visible}.pr .p{font:700 13px Cinzel,Georgia,serif;color:#ffd23f;text-align:right;white-space:nowrap}
.pr .nm{min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.pr .nm small{display:block}
.hs{display:grid;grid-template-columns:30px 1fr auto;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #ffd23f22}
.hs .stamp{font-size:9px;padding:2px 5px 1px;letter-spacing:1.5px;transform:rotate(-5deg)}
.hs small{display:block}
.mk-empty{color:#b89a6a;font-size:12px;padding:14px;text-align:center;border:1px dashed #d9a52044;border-radius:4px}
.mk-foot{display:flex;justify-content:flex-end;gap:6px;margin-top:12px}
/* ---- the trade screen */
.tr-vaults{display:grid;grid-template-columns:1fr 46px 1fr;gap:6px;align-items:stretch}
@media (max-width:460px){.tr-vaults{grid-template-columns:1fr}}
.vault{border:1px solid #d9a52066;border-radius:4px;padding:8px 10px;background:linear-gradient(#2b0810,#1f0509);min-height:130px;display:flex;flex-direction:column;min-width:0}
.vault.changed{animation:tr-flash 1s ease-out 2}
@keyframes tr-flash{0%,100%{box-shadow:none}50%{box-shadow:0 0 0 2px #ff7a59,0 0 18px #ff7a59aa}}
.vault h4{font:700 12px Cinzel,Georgia,serif;color:#ffd23f;margin:0 0 6px;display:flex;justify-content:space-between;align-items:center;gap:6px}
.vault h4 em{font:italic 11px Alegreya,Georgia,serif;color:#ff7a59}
.vault .it{display:flex;align-items:center;gap:6px;padding:3px 0;border-bottom:1px solid #ffd23f18}
.vault .it svg{width:24px;height:24px;margin:0;flex:none}#mb .vault .it button{padding:2px 6px;font-size:10px;margin-left:auto}
.vault .none{color:#8a6a3a;font-size:12px;padding:6px 0}
.coins{display:inline-flex;align-items:center;gap:5px;background:#3a2000;border:1px solid #d9a520;border-radius:12px;padding:3px 10px 3px 7px;color:#ffd23f;font:700 12px Cinzel,Georgia,serif;margin-top:6px;align-self:flex-start;white-space:nowrap}.coins svg{width:16px;height:16px;margin:0}
.vault .val{margin-top:auto;padding-top:6px;color:#d9b98a;font-size:11px}
.tr-mid{display:grid;place-items:center}
.tr-seal{width:42px;height:42px;border-radius:50%;background:#24060c;box-shadow:0 0 0 2px #d9a52066;display:grid;place-items:center;transition:box-shadow .3s}
.tr-seal img{width:38px;height:38px;border-radius:50%;filter:grayscale(.7) brightness(.6);transition:filter .3s}
.tr-seal.half img{filter:grayscale(.2) brightness(.9)}.tr-seal.both{box-shadow:0 0 0 2px #ffd23f,0 0 18px #ffd23f}.tr-seal.both img{filter:none}
.tr-fair{display:flex;align-items:center;gap:8px;margin:8px 0 4px;font-size:12px;color:#d9b98a}
.tr-fair .bar{flex:1;height:6px;background:#120306;border-radius:3px;overflow:hidden;display:flex;border:1px solid #000}
.tr-fair .bar i{height:100%;display:block}.tr-fair .bar .a{background:linear-gradient(90deg,#c98a10,#ffd23f)}.tr-fair .bar .b{background:linear-gradient(90deg,#39ff88,#1e9a52)}
.tr-warn{color:#ff7a59;font-weight:700;font-size:12px;margin:2px 0 6px}
.tr-bag{margin-top:8px}.tr-bag .g{grid-template-columns:repeat(auto-fill,minmax(44px,1fr));gap:3px}
.tr-bag .s{cursor:pointer;height:36px}.tr-bag .s:hover{border-color:#ffd23f}.tr-bag .s.no{opacity:.3;cursor:default}
.tr-coins{display:flex;gap:4px;flex-wrap:wrap;margin:8px 0 0}#mb .tr-coins button{padding:5px 8px;font-size:11px}
.tr-status{margin:10px 0 8px;font-size:12px;color:#d9b98a;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.tr-status b{color:#39ff88}.tr-status .dot{width:8px;height:8px;border-radius:50%;background:#8a6a3a;flex:none}.tr-status .dot.on{background:#39ff88;box-shadow:0 0 8px #39ff88}
.tr-acts{display:flex;gap:6px;align-items:center}
.tr-conf{text-align:center;margin:4px 0 8px}
.wax{width:78px;height:78px;border-radius:50%;margin:2px auto 8px;background:radial-gradient(circle at 36% 30%,#e0323f,#8c0c18 58%,#5a0610);box-shadow:inset 0 -3px 6px #0008,inset 0 3px 6px #fff3,0 4px 12px #000a;display:grid;place-items:center;transform:rotate(-6deg)}
.wax img{width:54px;height:54px;border-radius:50%;filter:grayscale(1) contrast(1.4) brightness(.9);mix-blend-mode:multiply;opacity:.85}
.wax.sealed{animation:wax-press .5s ease-out}
@keyframes wax-press{0%{transform:scale(1.5) rotate(-6deg);opacity:0}100%{transform:scale(1) rotate(-6deg);opacity:1}}
.tr-conf p{color:#d9b98a;font-size:12px;margin:0}
/* ---- the HUD: minimap ring, status pills, zoom and map buttons, the right-click menu */
#mm{border:3px solid #d9a520;box-shadow:0 0 0 2px #15030a,0 0 0 4px #6b4a06,0 6px 18px #000a}
.orb{background:linear-gradient(#2b0810,#15030a);border:1px solid #d9a520;box-shadow:0 0 0 2px #15030a;border-radius:10px;color:#f6eedc;font:700 10px/18px Cinzel,Georgia,serif;letter-spacing:.3px;overflow:hidden}
.orb i{opacity:.85;border-radius:9px 0 0 9px}
#cmp{background:#2b0810;border:2px solid #d9a520;box-shadow:0 0 0 2px #15030a;color:#ff7a59}
#wmb{background:linear-gradient(#7a1420,#4a0a12);border:1px solid #d9a520;box-shadow:0 0 0 2px #15030a;color:#ffe9b0;font:700 11px/20px Cinzel,Georgia,serif}
#zm button{font:700 14px/1 Cinzel,Georgia,serif;color:#ffe9b0;background:linear-gradient(#7a1420,#4a0a12);border:1px solid #d9a520;box-shadow:0 0 0 2px #15030a;border-radius:3px;width:30px;height:30px;padding:0}
#hint{font:700 12px Cinzel,Georgia,serif;color:#f6eedc}#hint b{color:#ffd23f}
#ctx{background:linear-gradient(#3b0b14,#24060c);border:1px solid #d9a520;box-shadow:0 0 0 2px #15030a,0 8px 20px #000c;border-radius:3px;min-width:150px;font:13px Alegreya,Georgia,serif;overflow:hidden}
#ctx div{padding:5px 10px;color:#f6eedc}#ctx div:hover{background:#d9a52033;color:#ffe9b0}
#ctx .h{background:#15030a;color:#ffd23f;font:700 11px Cinzel,Georgia,serif;letter-spacing:.3px;padding:5px 10px}

/* ---- the side panel, the chat scroll, the start screen and the world map */
:root{--p:#3b0b14;--p2:#15030a;--ink:#ffd23f}
#panel{background:radial-gradient(140% 70% at 50% 0%,#5a1220 0%,#3b0b14 45%,#24060c 100%);border:3px solid #15030a;box-shadow:inset 0 0 0 1px #d9a52055,0 0 0 1px #6b4a06,0 -8px 30px #0008;color:#f6eedc;font-family:Alegreya,Georgia,serif}
#tabs{background:#15030a;border-top:1px solid #d9a52066}
#tabs div{color:#d9b98a;border-top:2px solid transparent;font:700 10px/30px Cinzel,Georgia,serif}
#tabs div.on{background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);color:#2a1400;text-shadow:0 1px 0 #fff7;border-top-color:#6b4a06}
.s{background:#1a0408;border:1px solid #d9a52033;border-radius:3px}.s small{color:#ffd23f}
.sk{background:#1a040880;border:1px solid #ffd23f14;border-radius:3px;color:#f6eedc}.sk b{color:#ffd23f}
#pc{scrollbar-width:thin;scrollbar-color:#d9a520 #24060c}
#chat{background:#f3e6caf0;border:3px solid #15030a;box-shadow:0 0 0 2px #d9a520,0 0 0 3px #6b4a06;border-radius:3px;font-family:Alegreya,Georgia,serif}
#clog{scrollbar-color:#8a5a12 #0000}#cin{border-top-color:#8a5a1255}#cin b{color:#7a1420}
#cin input{background:#fff9;border:1px solid #d9a52088;font-family:Alegreya,Georgia,serif}#cin input:focus{border-color:#b8860b;background:#fff}
#sbox{background:radial-gradient(120% 70% at 50% 0%,#5a1220 0%,#3b0b14 48%,#24060c 100%);border:3px solid #15030a;outline:2px solid #d9a520;box-shadow:0 0 0 5px #24060c,0 0 0 6px #6b4a06,0 24px 60px #000d;border-radius:3px;color:#f6eedc;font-family:Alegreya,Georgia,serif}
#wm{background:#0d0407}#wmc{border:3px solid #d9a520;box-shadow:0 0 0 2px #15030a,0 0 0 4px #6b4a06}
.big{background:linear-gradient(#7a1420,#4a0a12);border:1px solid #d9a520;box-shadow:0 0 0 2px #15030a,inset 0 1px 0 #ffffff1f;color:#ffe9b0;border-radius:3px}
#bc,#bn,#nx{color:#2a1400;background:linear-gradient(#ffe88a,#f2b400 55%,#c98a10);border-color:#6b4a06;text-shadow:0 1px 0 #fff7}
.big:hover{filter:brightness(1.12)}

"""

# the theme goes after the game's own style block (the second <style> in the file)
k = h.find('</style>', h.find('</style>') + 1)
assert k > 0
h = h[:k] + CSS + h[k:]

# a screen that is not the market or the trade gets the normal width back
rep("const M=$('modal'),MB=$('mb');", "const M=$('modal'),MB=$('mb');new MutationObserver(()=>{if(MB.className&&!MB.querySelector('#mkroot,#trroot'))MB.className=''}).observe(MB,{childList:true});")

open(PATH, 'w', encoding='utf-8').write(h)
print('theme patch applied')
