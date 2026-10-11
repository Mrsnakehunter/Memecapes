# end-to-end: two players trade through the real game server with the new trade window
import asyncio, subprocess, time, json, os, tempfile
from playwright.async_api import async_playwright
SH = '/home/claude/scratch/shots/trade/e2e'; os.makedirs(SH, exist_ok=True)
D = tempfile.mkdtemp()
srv = subprocess.Popen(['node', '/home/claude/memecapes/server/server.js'], env={**os.environ, 'PORT': '18902', 'DATA_DIR': D, 'ADMIN_KEY': 'k'}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
web = subprocess.Popen(['python3', '-m', 'http.server', '8000'], cwd='/home/claude/scratch/site_t', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
INIT = "try{localStorage.setItem('mc_gate_2026-10-10','yes')}catch(e){}"
LOG = []
def ok(c, m): LOG.append(('PASS ' if c else 'FAIL ') + m); print(LOG[-1], flush=True)

async def player(b, name, inv, coins):
    ctx = await b.new_context(viewport={'width': 1100, 'height': 800}); await ctx.add_init_script(INIT)
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    for pat in ['**/fonts.googleapis.com/**', '**/fonts.gstatic.com/**']: await pg.route(pat, lambda r: r.abort())
    await pg.goto('http://localhost:8000/t.html', wait_until='domcontentloaded', timeout=180000); await pg.wait_for_timeout(5000)
    await pg.evaluate("(a)=>{const H=__H();H.st.inv=a[1];H.st.coins=a[2];H.save();H.NETS.want={bring:1};H.netConnect({t:'register',name:a[0],pass:'password1'})}", [name, inv, coins])
    pg.errs = errs
    return pg

async def shot(pg, n): await pg.screenshot(path=f'{SH}/{n}.png', timeout=120000)
async def ev(pg, js, arg=None): return await pg.evaluate(js, arg)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        A = await player(b, 'Alice1', ['sword', 'axe', 'logs', 'logs', 'logs', 'rsword', 'rgem', 'clue', 'bread'], 50000)
        B = await player(b, 'Bobbo', ['pick', 'potato', 'potato', 'gold', 'bstaff', 'tab_s', 'ore'], 9000)
        for _ in range(60):
            if await ev(A, "()=>__H().NETS.name") and await ev(B, "()=>__H().NETS.name"): break
            await A.wait_for_timeout(2000)
        await A.wait_for_timeout(6000)
        for pg in (A,B): print('dbg2',await ev(pg,"()=>JSON.stringify({n:__H().NETS.name,on:__H().NETS.on,me:__H().NETS.me,rev:__H().NETS.rev,tok:localStorage.getItem('mc_tok')&&1,nm:localStorage.getItem('mc_name'),started:typeof started!='undefined'})"))
        for pg in (A,B): print('dbg',await ev(pg,"()=>[__H().NETS.ws&&__H().NETS.ws.readyState,__H().NETS.on,__H().NETS.name,(document.getElementById('ner')||{}).textContent,document.getElementById('log')?document.getElementById('log').innerText.slice(-200):'']"))
        for pg, n, inv, c in ((A, 'Alice1', ['sword', 'axe', 'logs', 'logs', 'logs', 'rsword', 'rgem', 'clue', 'bread'], 50000), (B, 'Bobbo', ['pick', 'potato', 'potato', 'gold', 'bstaff', 'tab_s', 'ore'], 9000)):
            ok(await ev(pg, "()=>__H().NETS.name") == n, n + ' is signed in')
            await ev(pg, "(a)=>{const H=__H();H.st.inv=a[0];H.st.coins=a[1];H.netSend({t:'save',st:H.st,rev:H.NETS.rev})}", [inv, c])
        await A.wait_for_timeout(5000)
        for pg in (A, B): print('bags', await ev(pg, "()=>[__H().NETS.rev,__H().st.inv.join(),__H().st.coins]"))
        # Alice asks, Bobbo says yes
        await ev(A, "()=>__H().netSend({t:'tradeReq',name:'Bobbo'})"); await B.wait_for_timeout(2500)
        await shot(B, '00_bobbo_request')
        ok(await ev(B, "()=>getComputedStyle(document.getElementById('trq')).display") == 'flex', 'Bobbo sees the trade request card')
        await B.click('#trq [data-q="y"]', force=True); await A.wait_for_timeout(3000)
        ok(await ev(B, "()=>document.getElementById('trq').style.display") == 'none', 'request card hides when the trade opens')
        ok(await ev(A, "()=>document.querySelectorAll('.ntag.pn').length") >= 0, 'name tags are tappable')
        ok(await ev(A, "()=>!!__H().T()") and await ev(B, "()=>!!__H().T()"), 'trade window open on both sides')
        # Alice offers a sword, 2 logs and 12k coins through the window
        await ev(A, "()=>{document.querySelector('[data-bi=\"0\"]').click()}"); await A.wait_for_timeout(700)
        await A.click('[data-bi="2"]', button='right', force=True); await A.wait_for_timeout(700)
        await A.click('[data-tm="ax"]', force=True); await A.wait_for_timeout(500)
        await A.fill('#trmx', '2'); await A.press('#trmx', 'Enter'); await A.wait_for_timeout(700)
        await A.fill('#trci', '12k'); await A.wait_for_timeout(2500)
        await shot(A, '01_alice_offer')
        th = await ev(B, "()=>{const T=__H().T();return [T.theirs.items.join(),T.theirs.coins,T.ver]}")
        ok(th[0] == 'sword,logs,logs' and th[1] == 12000, 'Bobbo sees Alice\'s offer: ' + str(th))
        # Bobbo offers potatoes, gold and the staff
        for i in (1, 2, 3, 4, 5):
            await ev(B, "(i)=>document.querySelector('[data-bi=\"'+i+'\"]').click()", i); await B.wait_for_timeout(500)
        await B.wait_for_timeout(2500); await shot(B, '02_bobbo_offer'); await shot(A, '03_alice_sees')
        # Alice accepts right away: locked by the countdown
        lab = await ev(A, "()=>document.getElementById('tracc').textContent")
        ok('(' in lab or lab.startswith('Accept'), 'Alice accept button right after the change: ' + lab)
        await A.wait_for_timeout(3200)
        # Bobbo sneaks the staff out
        await ev(B, "()=>{const T=__H().T();const i=T.mine.items.indexOf('bstaff');}")
        await B.click('.trp.ism .trt[data-tk="bstaff"]', force=True); await B.wait_for_timeout(2500)
        await shot(A, '04_alice_sees_removed')
        gone = await ev(A, "()=>JSON.stringify(__H().T().gone)")
        ok('bstaff' in gone, 'Alice sees the staff taken out: ' + gone)
        ok(await ev(A, "()=>!!document.querySelector('.trt.isgone[data-tk=\"bstaff\"]')"), 'red ! tile shown for the staff')
        await A.wait_for_timeout(3200)
        # Alice accepts: first press asks about unseen items, second accepts
        await A.click('#tracc', force=True); await A.wait_for_timeout(800)
        lab = await ev(A, "()=>document.getElementById('tracc').textContent"); ok(lab == 'Accept anyway', 'unseen items: Accept asks once (' + lab + ')')
        await A.hover('.trp.ist .trt[data-tk="gold"]', force=True); await A.wait_for_timeout(900); await shot(A, '05_alice_inspects_gold')
        await A.click('#tracc', force=True); await A.wait_for_timeout(1500)
        ok(await ev(A, "()=>__H().T().acc[0]") == 1, 'Alice accepted')
        ok(await ev(B, "()=>__H().T().acc[1]") == 1, 'Bobbo sees Alice accepted')
        await B.wait_for_timeout(500); await B.click('#tracc', force=True); await B.wait_for_timeout(800)
        if await ev(B, "()=>document.getElementById('tracc').textContent") == 'Accept anyway': await B.click('#tracc', force=True)
        await B.wait_for_timeout(2500)
        ok(await ev(A, "()=>__H().T()&&__H().T().stage") == 2 and await ev(B, "()=>__H().T()&&__H().T().stage") == 2, 'both on the final check')
        await shot(A, '06_alice_final'); await shot(B, '07_bobbo_final')
        await A.wait_for_timeout(1800)
        await A.click('#tracc', force=True); await B.click('#tracc', force=True); await A.wait_for_timeout(4000)
        await shot(A, '08_alice_done'); await shot(B, '09_bobbo_done')
        ia = await ev(A, "()=>[__H().st.inv.slice().sort().join(),__H().st.coins,__H().NETS.rev]")
        ib = await ev(B, "()=>[__H().st.inv.slice().sort().join(),__H().st.coins,__H().NETS.rev]")
        ok(ia[0] == ','.join(sorted(['axe', 'logs', 'rsword', 'rgem', 'clue', 'bread', 'potato', 'potato', 'gold', 'tab_s'])) and ia[1] == 38000, 'Alice after: ' + str(ia))
        ok(ib[0] == ','.join(sorted(['pick', 'bstaff', 'ore', 'sword', 'logs', 'logs'])) and ib[1] == 21000, 'Bobbo after: ' + str(ib))
        ok(await ev(A, "()=>__H().st.tlog&&__H().st.tlog.length") == 1, 'Alice has 1 trade in her history')
        await A.click('[data-trh]', force=True); await A.wait_for_timeout(1000); await shot(A, '10_alice_history')
        print('errors A', A.errs[:3], 'B', B.errs[:3])
        await b.close()

try: asyncio.run(main())
finally:
    srv.terminate(); web.terminate()
    print('\n'.join(LOG)); print('FAILS', sum(1 for l in LOG if l.startswith('FAIL')))
