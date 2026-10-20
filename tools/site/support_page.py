#!/usr/bin/env python3
"""Puts the Support page (#support) into index.html: CSS, the page section, the nav link and the router title.
Idempotent: an existing Support page is replaced. The answers live in support/qa.json (tools/site/support_qa.py)."""
import re, sys

CSS = r"""
/* Support page (sp-*) */
.sp-hero{position:relative;text-align:center;padding:46px 0 10px}
.sp-crest{width:140px;height:140px;margin:0 auto 6px;display:block;filter:drop-shadow(0 0 28px rgba(255,210,63,.35))}
.sp-search{position:relative;max-width:760px;margin:22px auto 10px}
.sp-search input{width:100%;box-sizing:border-box;font:inherit;font-size:19px;padding:17px 54px 17px 20px;border-radius:16px;border:2px solid var(--gold2);background:#1d150c;color:var(--txt);outline:none;box-shadow:0 10px 40px rgba(0,0,0,.35),0 0 0 0 rgba(255,210,63,.0);transition:box-shadow .2s,border-color .2s}
.sp-search input:focus{border-color:var(--gold);box-shadow:0 10px 40px rgba(0,0,0,.35),0 0 0 4px rgba(255,210,63,.18)}
.sp-search input::placeholder{color:#8f7a55}
.sp-search svg{position:absolute;right:18px;top:50%;width:24px;height:24px;transform:translateY(-50%);pointer-events:none}
.sp-count{color:var(--mute);font-size:14px;text-align:center;margin:0}
.sp-count b{color:var(--gold)}
.sp-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:18px auto 0;max-width:980px}
.sp-chip{font:inherit;font-size:13.5px;font-weight:700;padding:7px 13px;border-radius:999px;border:1px solid var(--line);background:var(--bg2);color:var(--txt);cursor:pointer;transition:border-color .15s,background .15s}
.sp-chip:hover{border-color:var(--gold2)}
.sp-chip.on{background:var(--gold);color:#2b1d05;border-color:var(--gold)}
.sp-list{max-width:860px;margin:0 auto;display:flex;flex-direction:column;gap:10px}
.sp-h{display:flex;align-items:baseline;justify-content:space-between;gap:12px;max-width:860px;margin:0 auto 12px}
.sp-h h2{margin:0;font-size:22px}
.sp-h span{color:var(--mute);font-size:13.5px}
.sp-item{border:1px solid var(--line);border-radius:14px;background:linear-gradient(180deg,#2a1f14,#1d150c);overflow:hidden}
.sp-item.open{border-color:var(--gold2);box-shadow:0 10px 30px rgba(0,0,0,.3)}
.sp-qb{width:100%;display:flex;align-items:center;gap:12px;text-align:left;font:inherit;font-size:16.5px;font-weight:800;color:var(--txt);background:none;border:0;padding:15px 18px;cursor:pointer}
.sp-qb .sp-t{flex:none;font-size:11px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;color:#2b1d05;background:var(--gold2);border-radius:6px;padding:3px 7px}
.sp-qb .sp-ar{flex:none;margin-left:auto;width:22px;height:22px;transition:transform .2s;opacity:.8}
.sp-item.open .sp-ar{transform:rotate(180deg)}
.sp-a{display:none;padding:0 18px 16px;color:#e9dcc0;line-height:1.6;font-size:15.5px}
.sp-item.open .sp-a{display:block}
.sp-a p{margin:0 0 10px}
.sp-also{margin:10px 0 0;padding:10px 12px;border-radius:10px;background:rgba(255,210,63,.05);border:1px dashed var(--line);font-size:13px;color:var(--mute)}
.sp-also b{color:#d6c39a;font-weight:700}
.sp-also i{display:inline-block;margin:3px 6px 0 0;padding:2px 8px;border-radius:999px;background:#1d150c;border:1px solid var(--line);font-style:normal;color:#cdb98f}
.sp-none{max-width:860px;margin:0 auto;text-align:center;color:var(--mute);padding:28px 16px;border:1px dashed var(--line);border-radius:14px}
.sp-topics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;max-width:1140px;margin:0 auto}
.sp-topic{border:1px solid var(--line);border-radius:14px;padding:14px 16px;background:#1d150c;text-align:left;font:inherit;color:var(--txt);cursor:pointer;transition:border-color .15s,transform .15s}
.sp-topic:hover{border-color:var(--gold2);transform:translateY(-2px)}
.sp-topic b{display:block;font-size:15px;margin-bottom:3px}
.sp-topic span{color:var(--mute);font-size:12.5px}
.sp-contact{display:flex;gap:18px;align-items:center;max-width:860px;margin:0 auto;border:1px dashed var(--gold2);border-radius:16px;padding:18px 20px;background:rgba(255,210,63,.05)}
.sp-contact svg{flex:none;width:48px;height:48px}
.sp-contact p{margin:4px 0 0}
.sp-honest{text-align:center;color:var(--mute);font-size:14px;max-width:680px;margin:18px auto 0}
@media(max-width:860px){.sp-topics{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.sp-topics{grid-template-columns:1fr}.sp-search input{font-size:17px;padding:15px 48px 15px 16px}.sp-qb{font-size:15.5px;padding:13px 14px;flex-wrap:wrap;row-gap:6px}.sp-qb>span:nth-child(2){flex:1 1 100%;order:3}.sp-a{padding:0 14px 14px}.sp-contact{flex-direction:column;align-items:flex-start}.sp-h{flex-direction:column;gap:2px}}
"""

PAGE = r"""<main class="pg" id="pg-support" hidden>
<section class="sp-hero">
<svg class="sp-crest" viewBox="0 0 150 150" aria-hidden="true"><defs><linearGradient id="spg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff2a8"/><stop offset=".55" stop-color="#f2b400"/><stop offset="1" stop-color="#b9780c"/></linearGradient></defs>
<circle cx="75" cy="75" r="68" fill="none" stroke="#d9a520" stroke-width="1.5" stroke-dasharray="3 7" opacity=".7"/>
<circle cx="75" cy="75" r="58" fill="#1d150c" stroke="#5a3f1f" stroke-width="2"/>
<path d="M44 44 h62 v48 h-30 l-14 14 v-14 h-18 z" fill="url(#spg)" stroke="#2b1d05" stroke-width="2" stroke-linejoin="round"/>
<path d="M66 60 c0-7 6-10 10-10 s10 3 10 9 c0 6-8 7-8 14" fill="none" stroke="#2b1d05" stroke-width="5" stroke-linecap="round"/><circle cx="78" cy="83" r="3.2" fill="#2b1d05"/></svg>
<span class="pill gold">Support</span>
<h1>Ask anything.</h1>
<p class="lead">Every question a player has asked us, and the thousands we thought of before anyone asked. Type a few words. Answers are plain, honest and short.</p>
<div class="sp-search"><input id="spq" type="search" autocomplete="off" spellcheck="false" placeholder="e.g. I forgot my password, are there bots, how do I get the MemeCape" aria-label="Search the support answers"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="#ffd23f" stroke-width="2.4"/><path d="M15.5 15.5 L21 21" stroke="#ffd23f" stroke-width="2.6" stroke-linecap="round"/></svg></div>
<p class="sp-count" id="spcount">Loading the answers…</p>
<div class="sp-chips" id="spchips"></div>
</section>
<section style="padding-top:8px" id="spres"></section>
<section style="padding-top:0" id="sptopics"><div class="sec-title"><h2>Browse by topic</h2></div><div class="sp-topics" id="sptg"></div></section>
<section style="padding-top:0"><div class="sp-contact">
<svg viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="23" fill="none" stroke="#ffd23f" stroke-width="2.5"/><path d="M15 20 h22 v14 h-12 l-6 5 v-5 h-4 z" fill="none" stroke="#ffd23f" stroke-width="2.5" stroke-linejoin="round"/></svg>
<div><b style="font-size:18px;color:var(--gold)">Still stuck?</b><p class="mute"><span class="mc-contact"></span> In the game, <b>/report name reason</b> reports a player. We never message you first, and we never ask for passwords or seed phrases.</p></div>
</div>
<p class="sp-honest">Nothing here is financial or legal advice. Meme Coins are play money, and crypto can go to zero.</p>
<p style="text-align:center;margin-top:18px"><a class="btn gold" href="play.html">Play free</a> <a class="btn ghost" href="#faq">Read the FAQ</a></p></section>
</main>
"""

JS = r"""<script>(function(){var D=null,Q=document.getElementById('spq'),R=document.getElementById('spres'),C=document.getElementById('spchips'),G=document.getElementById('sptg'),N=document.getElementById('spcount'),TP=document.getElementById('sptopics');if(!Q)return;
var topic='',loading=false,X=[],TN={};
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function stem(w){return w.replace(/'s$/,'').replace(/(ing|ers|ed|es|s)$/,function(m){return w.length-m.length>=3?'':m})}
var STOP={'the':1,'a':1,'an':1,'i':1,'to':1,'is':1,'it':1,'in':1,'my':1,'do':1,'how':1,'what':1,'can':1,'of':1,'and':1,'on':1,'me':1,'for':1,'are':1,'does':1,'you':1,'be':1,'with':1,'there':1,'this':1,'that':1,'if':1,'or':1,'at':1,'get':1,'about':1,'why':1,'when':1,'where':1,'should':1,'any':1,'have':1,'has':1,'was':1,'will':1,'from':1,'please':1,'help':1,'know':1,'want':1,'need':1,'game':1,'memecapes':1,'capes':0};
function toks(s){return (s.toLowerCase().replace(/\$capez/g,'capestoken').replace(/[^a-z0-9\s]/g,' ').split(/\s+/)).filter(function(w){return w&&!STOP[w]}).map(stem)}
function fill(t,p,pl){return t.replace('{is}',pl?'are':'is').replace('{does}',pl?'do':'does').replace('{}',p)}
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1)}
function ways(e){var o=[];if(e.vp)D.vp.forEach(function(t){o.push(cap(fill(t,e.vp,0)))});if(e.np)D.np.forEach(function(t){o.push(cap(fill(t,e.np,e.pl)))});return o}
function prep(){X=D.qa.map(function(e,i){var w=ways(e);e.i=i;e.n=1+e.alts.length+w.length;e.ways=w;e.tq=toks(e.q+' '+(e.np||'')+' '+(e.vp||''));e.tq1=toks(e.alts.join(' '));e.tk=toks(e.k);e.ta=toks(e.a);return e});D.topics.forEach(function(t){TN[t.id]=t.name});var tot=X.reduce(function(s,e){return s+e.n},0);N.innerHTML='<b>'+tot.toLocaleString()+'</b> ways to ask, <b>'+X.length+'</b> answers, <b>'+D.topics.length+'</b> topics. No bots answering: the words are ours.';
C.innerHTML='<button class="sp-chip on" data-t="">All</button>'+D.topics.map(function(t){return '<button class="sp-chip" data-t="'+t.id+'">'+esc(t.name)+'</button>'}).join('');
G.innerHTML=D.topics.map(function(t){var n=X.filter(function(e){return e.t===t.id}).length;return '<button class="sp-topic" data-t="'+t.id+'"><b>'+esc(t.name)+'</b><span>'+n+' answers</span></button>'}).join('');
C.onclick=function(ev){var b=ev.target.closest('.sp-chip');if(!b)return;topic=b.getAttribute('data-t');[].forEach.call(C.children,function(x){x.classList.toggle('on',x===b)});render()};
G.onclick=function(ev){var b=ev.target.closest('.sp-topic');if(!b)return;topic=b.getAttribute('data-t');[].forEach.call(C.children,function(x){x.classList.toggle('on',x.getAttribute('data-t')===topic)});Q.value='';render();window.scrollTo({top:Q.getBoundingClientRect().top+window.pageYOffset-90,behavior:'smooth'})};
render()}
function score(e,qt){var s=0;qt.forEach(function(w){var hit=0;if(e.tq.indexOf(w)>=0)hit=4;else if(e.tq1.indexOf(w)>=0)hit=3;else if(e.tk.indexOf(w)>=0)hit=2.5;else if(e.ta.indexOf(w)>=0)hit=1;else{if(w.length>=4){for(var i=0;i<e.tq.length;i++)if(e.tq[i].indexOf(w)===0||w.indexOf(e.tq[i])===0&&e.tq[i].length>=4){hit=1.5;break}if(!hit)for(var j=0;j<e.tq1.length;j++)if(e.tq1[j].indexOf(w)===0){hit=1.5;break}if(!hit)for(var j=0;j<e.tk.length;j++)if(e.tk[j].indexOf(w)===0){hit=1.2;break}}}s+=hit});return s<1.5?0:s}
function render(){var q=Q.value.trim(),qt=toks(q),list,title,sub;
if(qt.length){list=X.map(function(e){return[score(e,qt),e]}).filter(function(x){return x[0]>0&&(!topic||x[1].t===topic)}).sort(function(a,b){return b[0]-a[0]||(b[1].top?1:0)-(a[1].top?1:0)}).slice(0,12).map(function(x){return x[1]});title=list.length?'Best answers':'No match';sub=list.length?list.length+' of '+X.length+' answers':''}
else if(topic){list=X.filter(function(e){return e.t===topic});title=TN[topic];sub=list.length+' answers'}
else{list=X.filter(function(e){return e.top});title='Most asked';sub='Pick a topic below or just type'}
TP.hidden=!!(qt.length||topic);
if(!list.length){R.innerHTML='<div class="sp-none">Nothing matched <b>'+esc(q)+'</b>. Try fewer words, or pick a topic. If it is not here, ask us on X and it will be.</div>';return}
R.innerHTML='<div class="sp-h"><h2>'+esc(title)+'</h2><span>'+esc(sub)+'</span></div><div class="sp-list">'+list.map(function(e,k){var r=Math.floor(Math.random()*Math.max(1,e.ways.length-3)),w=e.alts.slice(0,2).concat(e.ways.slice(r,r+2)).slice(0,4);return '<div class="sp-item'+(k===0&&qt.length?' open':'')+'"><button class="sp-qb" aria-expanded="'+(k===0&&qt.length)+'"><span class="sp-t">'+esc(TN[e.t])+'</span><span>'+esc(e.q)+'</span><svg class="sp-ar" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9 l6 6 6-6" fill="none" stroke="#ffd23f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button><div class="sp-a"><p>'+esc(e.a)+'</p>'+(w.length?'<div class="sp-also"><b>Also asked as</b> '+w.map(function(x){return '<i>'+esc(x)+'</i>'}).join('')+' <span style="opacity:.7">and '+(e.n-w.length)+' more</span></div>':'')+'</div></div>'}).join('')+'</div>'}
R.onclick=function(ev){var b=ev.target.closest('.sp-qb');if(!b)return;var it=b.parentNode,o=!it.classList.contains('open');it.classList.toggle('open',o);b.setAttribute('aria-expanded',o)};
var tm;Q.oninput=function(){clearTimeout(tm);tm=setTimeout(render,80)};
function load(){if(D||loading)return;loading=true;fetch('support/qa.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){D=j;prep()}).catch(function(){loading=false;N.textContent='The answers did not load. Reload the page, or ask us on X.'})}
function chk(){if((location.hash||'')==='#support')load()}addEventListener('hashchange',chk);chk();
})();</script>"""

def main():
    p = 'index.html'
    h = open(p, encoding='utf-8').read()
    # remove an earlier copy
    h = re.sub(r'\n/\* Support page \(sp-\*\) \*/.*?(?=\n</style>)', '', h, count=1, flags=re.S)
    h = re.sub(r'<main class="pg" id="pg-support" hidden>.*?</main>\n', '', h, count=1, flags=re.S)
    h = re.sub(r'<script>\(function\(\)\{var D=null,Q=document\.getElementById\(\'spq\'\).*?\}\)\(\);</script>', '', h, count=1, flags=re.S)
    h = h.replace('<a href="#support">Support</a>', '')
    h = h.replace(",support:'Support'", '')
    # css: before the last </style> in the head
    i = h.rfind('</style>', 0, h.find('<body'))
    assert i > 0
    h = h[:i] + CSS.rstrip('\n') + '\n' + h[i:]
    # page: before the Play page
    a = '<main class="pg" id="pg-play" hidden>'
    assert h.count(a) == 1
    h = h.replace(a, PAGE + a)
    # nav link after AI Agent
    a = '<a href="memesnake/">AI Agent</a>'
    assert h.count(a) == 1
    h = h.replace(a, a + '<a href="#support">Support</a>')
    # router title
    a = ",security:'Security'}"
    assert h.count(a) == 1
    h = h.replace(a, ",security:'Security',support:'Support'}")
    # script: before </body>
    i = h.rfind('</body>')
    assert i > 0
    h = h[:i] + JS + '\n' + h[i:]
    open(p, 'w', encoding='utf-8').write(h)
    print('Support page written')

if __name__ == '__main__':
    main()
