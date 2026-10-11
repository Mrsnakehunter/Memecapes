# screenshots of a UI flow: plan json = list of {name, js, wait, vw, vh}; runs on the test page with the HUD visible
import asyncio, subprocess, time, sys, json
from playwright.async_api import async_playwright
OUT='/home/claude/scratch/shots/trade'
INIT="try{localStorage.setItem('mc_gate_2026-10-10','yes')}catch(e){}"
async def main(plan,vw,vh,port):
    srv=subprocess.Popen(['python3','-m','http.server',str(port)],cwd='/home/claude/scratch/site',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
            ctx=await b.new_context(viewport={'width':vw,'height':vh},device_scale_factor=1,has_touch=vw<600,is_mobile=vw<600);await ctx.add_init_script(INIT)
            pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:errs.append('console:'+m.text[:200]) if m.type=='error' else None)
            for pat in ['**/fonts.googleapis.com/**','**/fonts.gstatic.com/**']: await pg.route(pat,lambda r:r.abort())
            await pg.goto(f'http://localhost:{port}/test7.html',wait_until='domcontentloaded',timeout=180000);await pg.wait_for_timeout(5000)
            await pg.evaluate("()=>document.getElementById('bg').click()");await pg.wait_for_timeout(9000)
            await pg.evaluate("()=>{const S=__S();S.st.gOff=1;S.st.gDone=1}")
            for job in plan:
                print('step',job['name'],flush=True)
                if job.get('js'): 
                    try: await pg.evaluate("()=>{"+job['js']+"}")
                    except Exception as e: errs.append('js:'+str(e)[:300])
                if job.get('hover'):
                    try: await pg.hover(job['hover'],timeout=20000,force=True)
                    except Exception as e: errs.append('hover:'+str(e)[:200])
                if job.get('rclick'):
                    try: await pg.click(job['rclick'],button='right',timeout=20000,force=True)
                    except Exception as e: errs.append('rclick:'+str(e)[:200])
                if job.get('click'):
                    try: await pg.click(job['click'],timeout=20000,force=True)
                    except Exception as e: errs.append('click:'+str(e)[:900])
                await pg.wait_for_timeout(job.get('wait',1500))
                if job.get('shot',1): await pg.screenshot(path=f'{OUT}/{job["name"]}.png',timeout=120000)
            print('errors',errs[:8]);await b.close()
    finally: srv.terminate()
a=sys.argv
asyncio.run(main(json.load(open(a[1])),int(a[2]) if len(a)>2 else 1100,int(a[3]) if len(a)>3 else 800,int(a[4]) if len(a)>4 else 8772))
