# fresh screenshots for memecapes.com: real game, HUD hidden, chosen time of day, no rain
import asyncio, subprocess, time, sys, json, os
from playwright.async_api import async_playwright
OUT='/home/claude/scratch/shots/site'; os.makedirs(OUT,exist_ok=True)
INIT="""try{localStorage.setItem('mc_gate_2026-10-10','yes')}catch(e){}
(()=>{const n=Date.now.bind(Date);Date.now=()=>n()+(window.__toff||0)})();
window.__day=(dp)=>{const n=Date.now()-(window.__toff||0);for(let k=0;k<400;k++){let t=n+k*60000;t=t-((t/1000)%1800)*1000+dp*1800*1000;if(((t/60000)%17)>=4.5&&((t/60000)%17)<16.5){window.__toff=t-n;return}}};"""
HIDE="body>*:not(#gl):not(.hm){visibility:hidden!important} #gl,.hm{visibility:visible!important}"   # coin hit markers stay in the shot
async def main(plan):
    srv=subprocess.Popen(['python3','-m','http.server',os.environ.get('PORT','8770')],cwd='/home/claude/scratch/site',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
            ctx=await b.new_context(viewport={'width':1100,'height':800});await ctx.add_init_script(INIT)
            pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
            for pat in ['**/fonts.googleapis.com/**','**/fonts.gstatic.com/**']: await pg.route(pat,lambda r:r.abort())
            await pg.goto('http://localhost:'+os.environ.get('PORT','8770')+'/'+os.environ.get('PAGE','test7.html'),wait_until='domcontentloaded',timeout=180000);await pg.wait_for_timeout(5000)
            await pg.evaluate("()=>document.getElementById('bg').click()");await pg.wait_for_timeout(7000)
            await pg.evaluate("()=>{const S=__S();S.st.gOff=1;S.st.gDone=1}")
            for job in plan:
                name=job['name'];print('shot',name,flush=True)
                await pg.evaluate("(dp)=>window.__day(dp)",job.get('day',.5))
                if job.get('setup'): await pg.evaluate("()=>{"+job['setup']+"}")
                if job.get('tp'): await pg.evaluate("(a)=>{const S=__S();const t=("+job['tp']+");__tp(t[0],t[1])}",None)
                await pg.wait_for_timeout(job.get('wait',14000))
                if job.get('act'): await pg.evaluate("()=>{"+job['act']+"}");await pg.wait_for_timeout(job.get('actwait',3000))
                await pg.evaluate("(c)=>__cam(c[0],c[1],c[2])",job['cam']);await pg.wait_for_timeout(job.get('camwait',5000))
                if job.get('pre'): await pg.evaluate("()=>{"+job['pre']+"}");await pg.wait_for_timeout(job.get('prewait',400))
                await pg.add_style_tag(content=HIDE)
                fr=job.get('frames',[0])
                for k,dl in enumerate(fr):
                    if dl: await pg.wait_for_timeout(dl)
                    await pg.screenshot(path=f'{OUT}/{name}_full.png' if len(fr)==1 else f'{OUT}/{name}_{k}.png',timeout=120000)
                await pg.evaluate("()=>{document.querySelectorAll('style').forEach(s=>{if(s.textContent.includes('#gl{visibility'))s.remove()})}")
            print('errors',errs[:5]);await b.close()
    finally: srv.terminate()
asyncio.run(main(json.load(open(sys.argv[1]))))
