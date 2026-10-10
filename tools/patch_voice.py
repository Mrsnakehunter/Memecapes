#!/usr/bin/env python3
"""MemeCapes' own words. Every name and line in the game is ours: the prayer book, the emotes, the
chat lines, the meme monsters' names, and the feature names (bounties, town tasks, loot log, meme hunts,
mastery capes, the Home Telly, Diamond Hands mode). Only display text changes; save keys stay the same.
Run from the repo root after patch_theme.py:  python3 tools/patch_voice.py
"""
import re, os
PATH = 'play.html'
DRY = os.environ.get('DRY')
h = open(PATH, encoding='utf-8').read()

# replacements never touch image data; the file is split into text and data-URI segments
SEG = re.split(r'(data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+)', h)
TXT = [i for i, s in enumerate(SEG) if not s.startswith('data:')]


def rep(old, new, count=1):
    n = sum(SEG[i].count(old) for i in TXT)
    if DRY and n != count:
        print(f'MISMATCH expected {count} found {n}: {old[:100]!r}', file=__import__('sys').stderr); return
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    for i in TXT:
        SEG[i] = SEG[i].replace(old, new)


# ---- the meme monsters: names that belong to someone else become ours
rep("MN=['Doge','Shiba Inu','Chill Guy','Pepe','Dogwifhat','Gigachad']", "MN=['Shibe','Shiba Inu','Vibe Dog','Froggo','Dogwifhat','Gigachad']")
rep("['bog','Pepe Bog Shaman'", "['bog','Bog Shaman'")
rep("quest:['Talk-to','Pepe']", "quest:['Talk-to','Froggo']")
rep("quest:'Pepe. The last free Original. Feels bad, man.'", "quest:'Froggo. The last free Original. Feels bad, man.'")
rep("Pepe needs proof you can fight.", "Froggo needs proof you can fight.")
rep("Return to Pepe.", "Return to Froggo.", 2)
rep("<h2>Pepe</h2>", "<h2>Froggo</h2>")
rep("""say("Pepe: 'Extremely unhelpful""", """say("Froggo: 'Extremely unhelpful""")
rep("You ratio Pepe.", "You ratio Froggo.")
rep("Pepe's Pond", "Froggo's Pond", 4)
rep("Pepe\\'s Pond", "Froggo\\'s Pond")
rep("'PepeFan'", "'FroggoFan'")
rep("'PEP'", "'FRG'")
rep("Frozen Doge", "Frozen Shibe", 13)
rep("'Doge pup'", "'Shibe pup'")
rep("['None','Doge','Shiba','WIF'", "['None','Shibe','Shiba','WIF'")
rep("Sandwich Doge", "Snack Shibe", 2)
rep("Feed it frost roots to melt the Doge.", "Feed it frost roots to melt the Shibe.")
rep("The brazier roars. The Doge has thawed!", "The brazier roars. The Shibe has thawed!")
rep("'WowDoge'", "'WowShibe'")
rep("'Moo Deng'", "'Bouncy Hippo'")
rep("'Peanut the Squirrel'", "'Nutty the Squirrel'")
rep("'Ghost of SafeMoon'", "'Ghost of Rugmoon'")

# ---- the prayer book: our names, our levels, our numbers (same slots, so saved prayers keep working)
rep("const PRY=[['Thick Skin',1,1,'def',.05],['Burst of Strength',4,1,'str',.05],['Clarity of Thought',7,1,'att',.05],['Rock Skin',10,6,'def',.1],['Superhuman Strength',13,6,'str',.1],['Improved Reflexes',16,6,'att',.1],['Rapid Restore',19,1,'rr',0],['Rapid Heal',22,2,'rh',0],['Protect Item',25,2,'pi',0],['Steel Skin',28,12,'def',.15],['Ultimate Strength',31,12,'str',.15],['Incredible Reflexes',34,12,'att',.15],['Protect from Magic',37,12,'oh',1],['Protect from Missiles',40,12,'oh',2],['Protect from Melee',43,12,'oh',3]];",
    "const PRY=[['Touch Grass',1,1,'def',.04],['Gym Arc',5,1,'str',.04],['Main Character',9,1,'att',.04],['Cope Shield',14,6,'def',.09],['Mewing',18,6,'str',.09],['Locked In',22,6,'att',.09],['Copium',26,1,'rr',0],['Self Care',29,2,'rh',0],['HODL',33,2,'pi',0],['Unbothered',37,12,'def',.16],['Sigma Grind',41,12,'str',.16],['Cracked',45,12,'att',.16],['Mute Magic',49,12,'oh',1],['Ratio Dodge',52,12,'oh',2],['Unbonkable',55,12,'oh',3]];")
rep("say('You have run out of prayer points, you can recharge at an altar.')", "say('Your prayer is spent. An altar refills it.')", 2)
rep("say('You have run out of prayer points, you can recharge at an altar.','#c00')", "say('Your prayer is spent. An altar refills it.','#c00')")

# ---- emotes: our list, our order; each one reuses an existing animation
rep("const EMO=['Yes','No','Bow','Angry','Think','Wave','Shrug','Cheer','Beckon','Laugh','Jump for Joy','Yawn','Dance','Jig','Spin','Headbang','Cry','Blow Kiss','Panic','Raspberry','Clap','Salute'];",
    "const EMO=['Stonks','GG','Ratio','Moon','Panic Sell','Cope','LOL','Wave','Yes','No','Hmm','Shrug','Dance','Griddy','Spin','Headbang','Rage','Come Here','Bored','Mwah','Clap','Sigma'],EMAP={Stonks:'Cheer',GG:'Bow',Ratio:'Raspberry',Moon:'Jump for Joy','Panic Sell':'Panic',Cope:'Cry',LOL:'Laugh',Hmm:'Think',Griddy:'Jig',Rage:'Angry','Come Here':'Beckon',Bored:'Yawn',Mwah:'Blow Kiss',Sigma:'Salute'};")
rep("Object.keys(EP).forEach(k=>PS['em:'+k]=EP[k]);", "Object.keys(EP).forEach(k=>PS['em:'+k]=EP[k]);Object.keys(EMAP).forEach(k=>PS['em:'+k]=EP[EMAP[k]]);")

# ---- chat lines in our voice
rep("say('New item added to your collection log: '+clNm(k),'#ff9040')", "say('Loot log: '+clNm(k)+' is yours now.','#ff9040')")
rep("""say("Congratulations, you've completed "+(c[1]==3?'an elite':c[1]==0?'an easy':'a '+CAT[c[1]][0].toLowerCase())+' combat task: '+c[0]+'.','#c77dff')""",
    """say('Combat feat done ('+CAT[c[1]][0].toLowerCase()+'): '+c[0]+'.','#c77dff')""")
rep("say('You have unlocked a new music track: '+TRK[tr]+'.','#c00')", "say('New tune: '+TRK[tr]+'.','#c00')")
rep("say('Well done! You have completed the '+d[0]+' diary. Your reward lamp is in your bag.','#0a0')", "say('Town tasks done: '+d[0]+'. Your reward lamp is in your bag.','#0a0')")

# ---- meme hunts (clues), strongboxes, wish lamps
rep("clue:['Clue scroll (easy)'", "clue:['Meme hunt (easy)'")
rep("<h2>Clue scroll (easy)</h2>", "<h2>Meme hunt (easy)</h2>")
rep("casket:['Casket',", "casket:['Strongbox',")
rep("'A clue! Read it to begin the trail.'", "'A clue! Read it to begin the hunt.'")
rep("'Treasure trail loot.'", "'Meme hunt loot.'", 2)
rep("say('A clue scroll! Read it to start a Treasure Trail.','#a60')", "say('A meme hunt scroll! Read it to start the hunt.','#a60')")
rep("""say("Well done, you've completed the Treasure Trail! Open the casket for your reward.",'#0a0')""", """say('Hunt complete! Open the strongbox for your reward.','#0a0')""")
rep("say('You find another clue scroll. Read it to continue.','#a60')", "say('You find the next hunt clue. Read it to continue.','#a60')")
rep("['clue','Finish a clue scroll']", "['clue','Finish a meme hunt']")
rep("['Clue scrolls',['casket','clhat','clcape']]", "['Meme hunts',['casket','clhat','clcape']]")
rep("'Antique lamp (large)'", "'Big wish lamp'")
rep("'Antique lamp'", "'Wish lamp'")
rep("Lamp Genie", "Wish Genie", 2)

# ---- bounties (the task skill)
rep("sl:'Slayer'", "sl:'Bounty'")
rep("slayer:['Talk-to','Slayer Master Bonkwell']", "slayer:['Talk-to','Bounty Boss Bonkwell']")
rep("""say("You've completed your task! Return to a Slayer master for a new one.",'#0a0')""", """say('Bounty done! See Bonkwell for a new one.','#0a0')""")
rep("['slay','Finish a Slayer task']", "['slay','Finish a bounty']")
rep("<h2>Slayer Master Bonkwell</h2>", "<h2>Bounty Boss Bonkwell</h2>")
rep('"I hunt memes for a living. Want a task?"', '"I hunt memes for a living. Want a bounty?"')
rep("Current task: kill <b>", "Current bounty: kill <b>")
rep("Skip task (30 points)", "Skip bounty (25 points)")
rep("Get a new task", "Get a new bounty")
rep("Slayer points: ", "Bounty points: ")
rep("' | Tasks done: '", "' | Bounties done: '")
rep("if((st.spts||0)<30)return say('You need 30 Slayer points to skip a task.');st.spts-=30;st.slay=null;say('Task skipped.')",
    "if((st.spts||0)<25)return say('You need 25 Bounty points to skip a bounty.');st.spts-=25;st.slay=null;say('Bounty skipped.')")
rep("'Task: kill <b>'", "'Bounty: kill <b>'")
rep("'No task. Visit Slayer Master Bonkwell in Wow Landing.'", "'No bounty. Visit Bounty Boss Bonkwell in Wow Landing.'")
rep("<span>Slayer level</span>", "<span>Bounty level</span>")
rep("Slayer XP per kill equals the monster\\'s Hitpoints.", "Bounty XP per kill equals the monster\\'s Health.")

# ---- feature names
rep("['log','Collection log'],['diary','Diaries'],['ca','Combat tasks'],['slay','Slayer'],['hs','Hiscores']", "['log','Loot log'],['diary','Town tasks'],['ca','Combat feats'],['slay','Bounty'],['hs','Leaderboards']")
rep("Collection log: <b>", "Loot log: <b>")
rep("<span>Collection log</span>", "<span>Loot log</span>")
rep("<span>Combat task points</span>", "<span>Combat feat points</span>")
rep("['Diaries',['lamp5','lamp15']]", "['Town tasks',['lamp5','lamp15']]")
rep("hp:'Hitpoints'", "hp:'Health'", 2)
rep("' Hitpoints');", "' Health');")
rep("fm:'Firemaking'", "fm:'Kindling'")
rep("'You need a Firemaking level of 10 to feed the brazier.", "'You need a Kindling level of 10 to feed the brazier.")
rep("'As an Ironman, you cannot use the Stock Market.'", "'In Diamond Hands mode you cannot use the Stock Market.'")
rep("'As an Ironman, you cannot trade.'", "'In Diamond Hands mode you cannot trade.'", 2)
rep("Ironman mode (no trading or Meme Exchange)", "Diamond Hands mode (no trading, no Stock Market)")
rep("'You are an Ironman. You stand alone. You will not be buying the dip.'", "'Diamond Hands mode. You stand alone. You never sell, because you cannot.'")
rep("['home','Cast Home Teleport']", "['home','Use the Home Telly']")
rep("say('You begin casting Home Teleport...','#1a4fb0')", "say('The Home Telly spins up...','#1a4fb0')")
rep(">Home Teleport'+(left?", ">Home Telly'+(left?")
rep("Teleport tablets from the shop and Meme Rings in every town work instantly.", "Telly tablets from the shop and the Meme Telly in every town work instantly.")
rep("['tab','Break a teleport tablet']", "['tab','Break a Telly tablet']")
rep("Deposit inventory</button>", "Bag in</button>")
rep("Deposit worn items</button>", "Gear in</button>")
rep("Placeholders: ", "Keep empty slots: ")
rep("its Cape of Accomplishment for 1,000,000 Meme Coins.", "its Mastery cape for 1,000,000 Meme Coins.")
rep("'He sells Capes of Accomplishment to level 100 masters.'", "'He sells Mastery capes to level 100 masters.'")
rep("your capes come trimmed.", "your capes get a gold border.")

# ---- items
rep("sbody:['Steel platebody'", "sbody:['Steel breastplate'")
rep("tinder:['Tinderbox'", "tinder:['Flint and steel'")
rep("say('You need a tinderbox to light a fire", "say('You need flint and steel to light a fire")
rep("'Big bones'", "'Large bones'")
rep("'Small fishing net'", "'Shrimp net'")
rep("'Stardust'", "'Star shards'")
rep("'Crashed star'", "'Fallen star'")
rep("'Crashed star (size '", "'Fallen star (size '", 2)

# ---- the right-click menu, in plain words
rep("'Talk-to'", "'Talk to'", 5)
rep("// --- Slayer\n", "// --- Bounties\n")
rep("// --- events, diaries, combat tasks, collection log", "// --- events, town tasks, combat feats, loot log")
rep("'Pray-at'", "'Pray at'")
rep("'Cook-at'", "'Cook at'")
rep("'Jump-across'", "'Jump across'")
rep("Walk here", "Go here", 3)
rep(">Examine</div>", ">Look</div>")
rep("['exa','Examine']", "['exa','Look']", 2)
rep("add('Examine',", "add('Look',")

# ---- our own combat level: defence and health, attack and strength, a little prayer and agility
rep("combatLvl=()=>Math.floor(.25*(lvl(st.xp.def)+lvl(st.xp.hp)+Math.floor(lvl(st.xp.pr||0)/2))+.325*(lvl(st.xp.at)+lvl(st.xp.str)))",
    "combatLvl=()=>Math.floor(.28*(lvl(st.xp.def)+lvl(st.xp.hp))+.34*(lvl(st.xp.at)+lvl(st.xp.str))+.1*lvl(st.xp.pr||0)+.08*lvl(st.xp.ag||0))")

# ---- until Froggo has a face of his own, the quest frog and the wild frogs use the bog frog model (never the old one)
rep("'k:pepe':'frogw'", "'k:pepe':'hexfrog'")
rep("(MDL.frogw&&MDL.frogw.ok?2.3:2.7)", "(MDL.hexfrog&&MDL.hexfrog.ok?2.3:2.7)")
rep("needMdl('frogw');if(MDL.frogw&&MDL.frogw.ok)", "needMdl('hexfrog');if(MDL.hexfrog&&MDL.hexfrog.ok)")
rep("qMdl(MDL.frogw,f.x,0,f.z,f.yaw,MDLSC.frogw,", "qMdl(MDL.hexfrog,f.x,0,f.z,f.yaw,MDLSC.hexfrog,")

rep("<span>Tasks done</span>", "<span>Bounties done</span>")
rep("<div class=\"h\">Choose Option</div>", "<div class=\"h\">What now?</div>", 2)
h = ''.join(SEG)
# nothing borrowed may remain in the text
left = [w for w in ['Pepe', 'Chill Guy', "'Doge'", 'Moo Deng', 'Peanut', 'SafeMoon', 'Thick Skin', 'Protect from', 'collection log', 'Slayer', 'Antique', 'Treasure Trail', 'Talk-to', 'Walk here', 'Hitpoints', 'Ironman', 'platebody', 'Tinderbox']
        if any(w in SEG[i] for i in TXT)]
if DRY: print('left:', left, file=__import__('sys').stderr)
else: assert not left, f'still in the text: {left}'
# the old flat pictures of Pepe and of the Doge photo are never drawn any more; they leave the file entirely
for k in ('pepe', 'stick'):
    h, n = re.subn(r'"%s": "data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", ' % k, '', h)
    assert n == 1, ('flat picture not found', k)
open(PATH, 'w', encoding='utf-8').write(h)
print('voice patch applied')
