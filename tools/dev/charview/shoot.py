#!/usr/bin/env python3
"""Character contact sheets without the game: skinned models, clips, held weapons (same grip maths as qHold).

usage: python3 tools/dev/charview/shoot.py job.json out.png      (run from the repo root)
job = {"cols":8,"w":1600,"h":800,"wcfg":{...},"wht":{...},
       "panels":[{"m":"knight","clip":"Attack","f":7,"cam":[yaw,pitch,dist,centre_y],"w":[{"k":"w_isword"},{"k":"w_rshield","left":1}],
                  "cfg":["f",100,20]}]}       (cfg: optional grip override for the right-hand weapon)
wcfg/wht: copy WCFG and WHT from the game (re.search(r'WHT=(\\{[^}]*\\})') etc.). Models face +z; cam yaw 0 = in front.
"""
import asyncio, json, sys, subprocess, time, os
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
async def main():
    job = json.load(open(sys.argv[1])); port = os.environ.get('VPORT', '8791')
    srv = subprocess.Popen(['python3', '-m', 'http.server', port], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            pg = await b.new_page(viewport={'width': job['w'], 'height': job['h']}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://localhost:{port}/tools/dev/charview/viewer.html'); await pg.wait_for_function('window.ready')
            await pg.evaluate('(j)=>{Object.assign(WCFG,j.wcfg||{});Object.assign(WHT,j.wht||{})}', job)
            await pg.evaluate('(j)=>render(j.panels,j.cols,j.w,j.h)', job)
            await pg.screenshot(path=sys.argv[2]); print('errors', errs[:5]); await b.close()
    finally: srv.terminate()
asyncio.run(main())
