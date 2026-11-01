#!/usr/bin/env python3
"""Render bag-icon pictures with iconview.html. usage: python3 tools/dev/charview/shoot_icon.py jobs.json
jobs.json = [{"url": "/path/served/from/the/repo/root.json", "out": "pic.png", "yaw":..,"pitch":..,"dist":..,"fov":..}, ...]
(url paths are served from the repo root; put cut models under scratch/ or tools/dev/charview/)"""
import asyncio, json, sys, subprocess, time, os
from playwright.async_api import async_playwright
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
async def main():
    jobs = json.load(open(sys.argv[1])); port = os.environ.get('VPORT', '8792')
    srv = subprocess.Popen(['python3', '-m', 'http.server', port], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            pg = await b.new_page(viewport={'width': 1024, 'height': 1024}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://localhost:{port}/tools/dev/charview/iconview.html'); await pg.wait_for_function('window.ready')
            for j in jobs:
                await pg.evaluate('(j)=>render(j)', j)
                await pg.locator('#c').screenshot(path=j['out'], omit_background=True); print('rendered', j['out'])
            print('errors', errs[:5]); await b.close()
    finally: srv.terminate()
asyncio.run(main())
