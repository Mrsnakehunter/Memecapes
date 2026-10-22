#!/usr/bin/env python3
"""The Support page's knowledge base: writes support/qa.json from the entries below.

Each entry: topic, canonical question, answer, extra phrasings, a verb phrase (vp) and/or a noun phrase (np).
The page builds the "ways to ask" from vp/np templates in the browser, so the file stays small. Answers must
never give away how the guards work (thresholds, timings, commands, addresses) and never mention dates or prices.
Run from the repo root:  python3 tools/site/support_qa.py
"""
import json, os, re

T = {}  # topic id -> name, in display order
def topic(i, n): T[i] = n
topic('start', 'Getting started')
topic('account', 'Accounts and login')
topic('online', 'Online play and chat')
topic('skills', 'Skills')
topic('combat', 'Combat and monsters')
topic('items', 'Items, bag and bank')
topic('world', 'Towns and travel')
topic('quests', 'Quests')
topic('capes', 'Capes')
topic('coins', 'Meme Coins and $CAPES')
topic('skins', 'Skins and the Wardrobe')
topic('trade', 'Trading and the Stock Market')
topic('shop', 'The Shop')
topic('launch', 'Launchpad')
topic('stream', 'Watch and Stream')
topic('agent', 'The AI Agent')
topic('safety', 'Safety and scams')
topic('tech', 'Technical problems')
topic('rules', 'Rules, terms and privacy')
topic('about', 'About MemeCapes')

E = []
def q(t, question, answer, alts=(), vp=None, np=None, k='', top=False):
    assert t in T, t
    assert not re.search(r'\b20\d\d\b|\$\d', answer + question), question  # no dates, no prices in the knowledge base
    E.append({'t': t, 'q': question, 'a': answer, 'alts': list(alts), 'vp': vp, 'np': np, 'k': k, 'top': top})

# ---------------------------------------------------------------- weekly agent battle (in the Pit)
q('trade', 'What is the Weekly Agent Battle?',
  'A weekly contest in snakepit, the trading app next to the game. Pick an AI agent (Turtle plays it safe, Snake is balanced, Wild swings big) and one lucky coin from the week\'s board of five. The agent trades for you all week and the best % return on Sunday evening wins. Right now every week is a practice week: live prices, practice SOL, free to join, and nothing is paid in or out.',
  ['How does the agent battle work?', 'What is the AI trading contest?', 'What is the battle in the Pit?', 'How do I join the battle?'], np='the Weekly Agent Battle', k='battle agent contest weekly turtle snake wild boost leaderboard', top=True)
q('trade', 'What does BOOST do in the battle?',
  'Once a day you can press BOOST on your battle card. For the next 24 hours your agent bets one step bigger on each trade, up to the safety limit. When to press it is your call: it is the one move you make during the week. Everything else locks when the week starts.',
  ['How does BOOST work?', 'Can I change my agent during the week?', 'What can I change after the battle starts?'], np='BOOST', k='boost battle bet lock change')
q('trade', 'Does the battle use real money?',
  'Not yet. Battle weeks are practice weeks: the prices are real but the SOL is practice SOL, entry is free and nobody is paid in or out. Real SOL weeks only open once the money can be held safely on-chain and the rules have had a legal review. It is not financial advice: trading can lose money.',
  ['Can I win real SOL in the battle?', 'Is the battle free?', 'Do I pay to join the battle?'], np='the battle prizes', k='battle real money practice free paper prize')

# ---------------------------------------------------------------- getting started
q('start', 'How do I play MemeCapes?',
  'Open memecapes.com in a browser on your phone or computer and press Play free. There is nothing to download and no wallet is needed. Tap the ground to walk, tap a tree, rock, fishing spot or monster to use it, and follow the starter guide card in the top left for your first few minutes.',
  ['How do I start playing?', 'Where do I play the game?', 'Is there a download?', 'How do I get into the game?'], vp='play the game', np='the game', k='start begin play new', top=True)
q('start', 'Is MemeCapes free?',
  'Yes. The game is free to play in your browser. You do not need an account to try it and you never need crypto to play. The only things that cost money are optional: the shop, skins, the streamer pass and the launchpad.',
  ['Does it cost anything?', 'Is it free to play?', 'Do I have to pay to play?', 'Is there a subscription?'], np='the cost of playing', k='free cost price pay', top=True)
q('start', 'Does MemeCapes work on my phone?',
  'Yes. The game is built phone first and runs in the phone browser (Chrome, Safari, Samsung Internet and others). Hold the phone upright, tap to walk, drag to turn the camera and pinch to zoom. Older or very cheap phones can feel slow in big towns: turn shadows off in the settings.',
  ['Can I play on iPhone?', 'Can I play on Android?', 'Is there a mobile version?', 'Does it work on a tablet?', 'Is there an app?'], vp='play on my phone', np='the phone version', k='mobile iphone android tablet ipad app', top=True)
q('start', 'Do I need to download anything?',
  'No. MemeCapes runs entirely in your browser. There is no installer, no app store download and no launcher. Bookmark memecapes.com and you are set.',
  ['Is there an app to install?', 'Where is the download link?', 'Can I get it on Steam?'], np='the download', k='download install app steam')
q('start', 'How do I move my character?',
  'Tap or click the ground where you want to go and your character walks there. Tap something in the world (a tree, a rock, a fishing spot, a monster, a person) to use it. On a computer you can also click and drag to turn the camera.',
  ['How do I walk?', 'How do the controls work?', 'What are the controls?', 'How do I move around?'], vp='move my character', np='the controls', k='walk move controls click tap')
q('start', 'How do I turn the camera?',
  'Drag on the screen (or click and drag with the mouse) to turn the camera around your character. Use pinch, the mouse wheel or the + and - buttons to zoom. Massive buildings and the castle turn see-through when they block the view; everything else stays, so turn the camera yourself.',
  ['How do I rotate the view?', 'How do I zoom in and out?', 'The camera is stuck behind a building'], vp='turn the camera', np='the camera', k='camera rotate zoom view')
q('start', 'What is the starter guide?',
  'The small card in the top left of the game walks you through your first few minutes: walk, meet Froggo, chop a tree, light a fire, catch shrimps, cook them, mine some ore, defeat a weak meme and visit a bank. A gold arrow points to the nearest thing you need. Finishing it pays Meme Coins and a small XP lamp. The x hides it and the small ? brings it back.',
  ['What is the card in the corner?', 'How do I get the tutorial back?', 'I closed the guide by accident', 'Where is the tutorial?'], np='the starter guide', k='tutorial guide card arrow help')
q('start', 'What should I do first?',
  'Follow the starter guide: chop a tree, light a fire, fish and cook a few shrimps, mine some copper, then fight a level 1 Wojak Wanderer outside the castle. Then talk to Froggo by the castle gate for your first quest, and walk down the road to Wow Landing, the first town.',
  ['What do I do when I start?', 'Where do I begin?', 'I am new, what now?', 'Beginner tips'], np='the first things to do', k='beginner new first tips')
q('start', 'Where do I start in the game?',
  'Every new adventurer wakes up in the courtyard of Castle Gigachad with a wiped wallet, a bronze sword, an axe, a pickaxe, a tinderbox, a net and some bread. Froggo waits by the gate, the fields outside have level 1 memes, and the road leads to Wow Landing.',
  ['Where does my character spawn?', 'What is the starting town?', 'Where is Castle Gigachad?'], np='the starting area', k='spawn castle gigachad start')
q('start', 'What gear do I start with?',
  'A bronze sword, a bronze axe, a bronze pickaxe, a tinderbox, a shrimp net and some bread. That is enough to fight, chop, mine, make fires and fish on day one.',
  ['What items do new players get?', 'Starting equipment'], np='the starting gear', k='starter gear items bronze')
q('start', 'Can I change how my character looks?',
  'Yes. On the start screen you pick skin, hair, shirt, pants, boots and whether your adventurer is male or female. Capes and skins you earn or buy later change the look too. Looks never change your stats.',
  ['How do I customise my character?', 'Can I pick a female character?', 'Can I change my hair?'], vp='change my appearance', np='character customisation', k='appearance look hair skin outfit female male')
q('start', 'What is a Normie?',
  'You. In the story, Normies are the only people in MemeCapes who are not made of Clout, which means the Rugpuller cannot edit or control you. That is why Froggo recruits you.',
  ['Why am I called a Normie?', 'What does Normie mean?'], np='a Normie', k='normie story')
q('start', 'How do I zoom in or out?',
  'Pinch on a phone, use the mouse wheel on a computer, or press the + and - buttons on the screen.',
  ['Can I zoom the camera?', 'The game is too zoomed in'], vp='zoom in', k='zoom pinch wheel')
q('start', 'Can I play on a computer?',
  'Yes. Any modern browser on Windows, Mac, Linux or ChromeOS works. Click to walk, click and drag to turn the camera, and use the mouse wheel to zoom.',
  ['Does it work on PC?', 'Can I play on a Mac?', 'Does it run on a Chromebook?'], vp='play on a computer', k='pc mac windows laptop chromebook desktop')
q('start', 'Which browser works best?',
  'Any current browser works: Chrome, Safari, Firefox, Edge, Samsung Internet and Brave. If something looks wrong, update the browser first; very old browsers cannot run the 3D world.',
  ['Does it work in Safari?', 'Does it work in Firefox?', 'Best browser for the game'], np='browser support', k='browser chrome safari firefox edge brave')
q('start', 'How long does it take to load?',
  'The first visit downloads the world and its models, so give it a few seconds on a good connection and a little longer on mobile data. Later visits are faster because the browser keeps the files.',
  ['Why is the game loading slowly?', 'It is stuck on loading'], np='loading time', k='load loading slow stuck')
q('start', 'Is there a story?',
  'Yes: The Great Rug. The internet became a world, the Seven Originals built the towns and wove their Clout into seven capes, and one of them, the Dev, drained the Liquidity and became the Rugpuller. You are the Normie he cannot edit. Read the full story on the Story page.',
  ['What is the game about?', 'What is the plot?', 'Who is the Rugpuller?'], np='the story', k='story plot lore rug rugpuller')
q('start', 'Who are the Seven Originals?',
  'The first memes: Shibe, Froggo, Wojak, Chad, Stonks Guy, Moon and the Dev. Each wove their Clout into an OG Cape. The Dev corrupted his and became the Rugpuller; the other six capes are scattered across the world and the story chapters are about getting them back.',
  ['What are the OG Capes?', 'Who are the Originals?'], np='the Seven Originals', k='originals og capes story')
q('start', 'What is Clout?',
  'In the story, Clout is the magic of being seen: the power that memes are made of. The Seven Originals wove theirs into capes, and those capes kept the world\'s Liquidity flowing until the Rug.',
  ['What does Clout mean in the story?'], np='Clout', k='clout story magic')

# ---------------------------------------------------------------- accounts and login
q('account', 'Do I need an account?',
  'Not to try the game: you can play as a guest and the game saves in your browser. To play online with other people, keep your progress across devices, chat and trade, create a free account on the start screen.',
  ['Can I play without signing up?', 'Is an account required?', 'Can I play as a guest?'], np='an account', k='account guest signup required', top=True)
q('account', 'How do I create an account?',
  'On the start screen choose Create Account, pick a username (3 to 12 letters, numbers or underscores, no spaces) and a password of at least 8 characters that you do not use anywhere else. That is all: no email, no wallet, no phone number.',
  ['How do I sign up?', 'How do I register?', 'Make a new account'], vp='create an account', k='create register sign up username password', top=True)
q('account', 'What are the username rules?',
  'Usernames are 3 to 12 characters long and can only use letters, numbers and underscores. No spaces, no symbols. Your username is shown to other players above your head and in chat.',
  ['Why is my username rejected?', 'Can I use spaces in my name?', 'How long can a username be?'], np='the username rules', k='username name rules characters')
q('account', 'Can I change my username?',
  'Not at the moment. Pick a name you are happy to wear, because it is shown above your head and in chat. If you really need a different name, start a new account.',
  ['How do I rename my character?', 'Change my display name'], vp='change my username', k='rename username change name')
q('account', 'What are the password rules?',
  'At least 8 characters. Use a password you do not use on any other site, ideally from a password manager. MemeCapes never emails you, so nobody from MemeCapes will ever ask for it.',
  ['How long must my password be?', 'Password requirements'], np='the password rules', k='password rules length')
q('account', 'I forgot my password. How do I reset it?',
  'There is no automatic reset yet, because accounts have no email or phone attached (we keep what we know about you to a minimum). Keep your password somewhere safe. If you are locked out, message @Mrsnakebaby on X from the account you play with and we will see what can be done, but we cannot promise recovery.',
  ['Forgot password', 'Can I recover my account?', 'How do I reset my password?', 'I lost my password'], vp='reset my password', np='password recovery', k='forgot reset recover password lost locked out', top=True)
q('account', 'Can I change my password?',
  'Not from inside the game yet. If your password may have leaked, stop using it elsewhere and message @Mrsnakebaby on X so we can help secure the account.',
  ['How do I update my password?'], vp='change my password', k='change password update')
q('account', 'Why does it say "Could not reach the game server"?',
  'The game could not open its connection to the server. The usual causes: you are on plain http instead of https (the site now sends you to https automatically; reload once), a very strict network or VPN is blocking the connection, or the server is being restarted. Wait a minute and try again. You can always choose Play offline in the meantime; an offline game saves in your browser.',
  ['Can\'t connect to the server', 'Login says the server is unreachable', 'Server down?', 'Could not reach the game server', 'The game will not let me log in'], np='the "could not reach the game server" message', k='server unreachable connect login error offline', top=True)
q('account', 'Is the server down?',
  'If the start screen shows an online player count, the server is up. If it says Offline or Reconnecting, wait a minute and reload. Short restarts happen when we ship updates; you can play offline meanwhile.',
  ['How do I check if the server is online?', 'Server status'], np='the server status', k='server status down online')
q('account', 'Where is my progress saved?',
  'With an account, on the game server, so you can log in from any device. As a guest or offline, only in your browser\'s local storage on that device: clearing site data, private browsing or switching devices can lose it.',
  ['Is my save in the cloud?', 'Will I lose progress if I clear my browser?', 'Does the game save automatically?'], np='saving', k='save cloud progress local storage', top=True)
q('account', 'Can I play on another device with the same account?',
  'Yes. Log in with your username and password on any phone or computer and your character, bag, bank and skills come with you. Only one device can be logged in at a time.',
  ['Can I switch between phone and PC?', 'Can I use my account on two devices?'], vp='use my account on another device', k='device switch phone pc cross')
q('account', 'Can I move my guest progress into an account?',
  'When you create an account on the device where you played as a guest, the game offers to carry your local progress over. After that the account save is the one that counts.',
  ['Will I lose my guest save if I register?', 'Transfer offline progress to my account'], vp='keep my guest progress', k='guest transfer progress offline')
q('account', 'How do I log out?',
  'Type /logout in the chat box, or close the tab. Logging out on a shared device keeps your account safe.',
  ['Where is the logout button?'], vp='log out', k='logout sign out')
q('account', 'Can I have more than one account?',
  'You can make more than one, but please play fair: using several accounts to cheat, farm or get around a ban is against the rules and can get all of them suspended.',
  ['Are alts allowed?', 'Can I make a second account?'], np='multiple accounts', k='alt second account multiple')
q('account', 'Can I delete my account?',
  'Yes. Message @Mrsnakebaby on X from the account you play with and ask for the account to be deleted. Deleting is final: the character, items and Meme Coins are gone.',
  ['How do I remove my account?', 'Delete my data'], vp='delete my account', k='delete remove account data')
q('account', 'How old do I have to be?',
  'You must be 18 or older to use MemeCapes. The game has crypto features, so it is not for children, and we do not knowingly collect anything from anyone under 18.',
  ['Is there an age limit?', 'Can kids play?', 'Is it 18+?'], np='the age limit', k='age 18 kids children minimum')
q('account', 'What is the age gate when I open the site?',
  'The first time you visit, the site asks you to confirm you are 18 or older and that you agree to the Terms and the Privacy Policy. It remembers your answer in your browser and asks again only when the terms change.',
  ['Why does the site ask my age?', 'The 18+ box keeps coming back'], np='the age gate', k='age gate terms accept')
q('account', 'Why was I logged out?',
  'The game logs you out when the same account logs in somewhere else, when the connection drops for too long, or when the server restarts for an update. Just log in again; your progress is saved on the server.',
  ['I keep getting disconnected', 'Why did the game kick me?'], np='being logged out', k='logged out kicked disconnected')
q('account', 'Someone else is using my account. What do I do?',
  'Log in and the other session is kicked. Then stop using that password anywhere, and message @Mrsnakebaby on X so we can help lock things down. Never share your password, even with someone who says they are from MemeCapes.',
  ['My account was hacked', 'Someone stole my account'], np='a stolen account', k='hacked stolen account compromised')
q('account', 'Why does my login say the name is locked?',
  'Too many wrong passwords in a row lock a name for a short while to stop password guessing. Wait a bit and try again carefully.',
  ['Account temporarily locked', 'Too many login attempts'], np='a locked name', k='locked attempts wrong password')
q('account', 'Does MemeCapes send emails?',
  'No. Accounts have no email, and MemeCapes never emails or messages you first. Any email or DM that claims to be from MemeCapes is fake.',
  ['Will you email me?', 'I got an email from MemeCapes'], np='emails from MemeCapes', k='email dm message fake')

# ---------------------------------------------------------------- online play and chat
q('online', 'Is MemeCapes multiplayer?',
  'Yes. With an account you see other players walking the world, chat with them, and trade with them. The start screen shows how many real players are online right now.',
  ['Can I see other players?', 'Is it an MMO?', 'Can I play with friends?'], np='multiplayer', k='multiplayer mmo online friends', top=True)
q('online', 'How do I chat?',
  'Open the chat box at the bottom of the screen, type and press enter. Messages are short (80 characters) and appear above your head and in the chat log. Be kind: the rules apply in chat.',
  ['Where is the chat?', 'How do I talk to other players?'], vp='chat', np='the chat', k='chat talk message')
q('online', 'What chat commands are there?',
  '/who lists the players online, /trade name sends a trade request, /ignore name hides a player, /unignore name shows them again, /report name reason reports a player, and /logout logs you out.',
  ['List of slash commands', 'What does /who do?', 'Chat commands'], np='the chat commands', k='commands slash who trade ignore report logout')
q('online', 'How do I see who is online?',
  'Type /who in the chat. The start screen also shows the number of real players online.',
  ['Who is online right now?'], vp='see who is online', k='who online players')
q('online', 'How do I ignore someone?',
  'Type /ignore followed by their name. You will no longer see their chat or trade requests. /unignore turns it back.',
  ['How do I mute a player?', 'Block a player', 'Someone is spamming me'], vp='ignore a player', k='ignore mute block spam')
q('online', 'How do I report a player?',
  'Type /report, their name and a short reason, for example /report name scamming. Reports go to the team. For anything urgent or with screenshots, message @Mrsnakebaby on X.',
  ['Report cheating', 'Report harassment', 'Someone scammed me'], vp='report a player', k='report cheat harass scam')
q('online', 'Are there bots in the game?',
  'Yes. To keep the world lively while it grows, MemeCapes has a few dozen bots: computer-controlled characters that look and act like players. They walk around, chat, chop trees, fish and mine. They never trade, never use the Stock Market and never take your kills or resources, and there are fewer of them as more real people play. Bots are never counted as players in anything we post.',
  ['Are the other players real?', 'Is that player an NPC?', 'Why does nobody answer my trade request?', 'Fake players'], np='bots', k='bots npc fake players real', top=True)
q('online', 'How do I tell a bot from a real player?',
  'You usually cannot, and that is on purpose. The clue is behaviour: bots never accept trades and never use the Stock Market. The online count on the start screen and /who only count real people.',
  ['Can I trade with a bot?', 'Which players are bots?'], vp='tell bots and players apart', k='bots real tell apart')
q('online', 'What happens when I lose connection?',
  'The game says it is reconnecting and tries again on its own. Your last save is on the server. If a trade was open it closes safely: nothing is swapped unless both sides had already pressed accept.',
  ['The game keeps reconnecting', 'I lost connection mid-trade'], np='losing connection', k='reconnect connection lost dropped')
q('online', 'Can I play offline?',
  'Yes. Choose Play offline (or Guest) on the start screen. The world, skills, quests and monsters all work; you just will not see other players, chat or trade, and the save lives in that browser only.',
  ['Does the game work without internet?', 'Single player mode'], vp='play offline', np='offline mode', k='offline single player')
q('online', 'Why is the online player count so low?',
  'Because it counts real people only, never bots. The game is new and grows every week.',
  ['Only a few players online'], np='the online count', k='online count players low')
q('online', 'Can I message a player privately?',
  'Not yet. Chat is public to the people around you. Private messages and friends lists are on the list for later.',
  ['Is there a friends list?', 'Private messages', 'DM a player'], np='private messages', k='private message friends dm whisper')
q('online', 'Why can\'t I see my friend?',
  'You both need to be logged in to accounts (not guests or offline) and standing near each other in the world: the game shows people within sight of you, not the whole map. Check the start screen says Online, then meet at a landmark like Froggo at the castle gate.',
  ['My friend and I cannot see each other', 'How do I find my friend in game?'], vp='find my friend', k='friend see each other meet')
q('online', 'Is the chat moderated?',
  'Yes. Reports are read, and players who harass, scam or spam can be muted or banned. Links in chat are limited to keep scams out.',
  ['Can I post links in chat?', 'Who moderates the chat?'], np='chat moderation', k='moderation links rules chat')
q('online', 'What is the Meme Telly?',
  'The glowing ring in every town. Step in and it teleports you to any town you have already walked into once. The Grand Tour quest unlocks all eight.',
  ['What is the ring in town?', 'How do I fast travel?'], np='the Meme Telly', k='telly ring teleport fast travel')

# ---------------------------------------------------------------- skills
q('skills', 'What skills are there?',
  'Fifteen: Attack, Strength, Defence, Health, Prayer, Woodcutting, Mining, Fishing, Cooking, Smithing, Kindling, Agility, Bounty, Farming and Construction. Each goes to level 100, and each has a cape at 100.',
  ['How many skills are in the game?', 'List of skills'], np='the skills', k='skills list fifteen', top=True)
q('skills', 'How do I level up a skill?',
  'Use it. Every chop, catch, cook, smelt, kill or plant gives XP in its skill, and levels come from XP. XP lamps (from quests, random events and the starter guide) give a chunk of XP in a skill of your choice.',
  ['How does XP work?', 'How do I gain experience?'], vp='level up', np='levelling', k='level xp experience gain')
q('skills', 'What is the maximum level?',
  'Level 100 in every skill. At 100 the Cape merchant sells you that skill\'s cape; two skills at 100 and your capes come with a gold trim.',
  ['What is the level cap?', 'Can I go past 99?'], np='the level cap', k='max level cap 100')
q('skills', 'How does Woodcutting work?',
  'Tap a tree with an axe in your bag. Higher Woodcutting levels chop faster and better axes help too. Logs feed fires (Kindling), become planks at the sawmill (Construction) and sell to shops.',
  ['How do I chop trees?', 'How do I get logs?'], vp='chop trees', np='Woodcutting', k='woodcutting chop trees logs axe')
q('skills', 'How does Fishing work?',
  'Tap the bubbling spots in the water with a net in your bag. Shrimps come first; better spots and fish come with levels. Froggo\'s Pond has fishing spots right off the boardwalks.',
  ['How do I fish?', 'Where are fishing spots?'], vp='fish', np='Fishing', k='fishing net shrimp spots')
q('skills', 'How does Cooking work?',
  'Carry raw food and tap a fire you lit or a cooking range in any town. Low levels burn some of the food; burnt ones still count as practice.',
  ['How do I cook?', 'Why does my food burn?'], vp='cook food', np='Cooking', k='cooking cook burn range fire')
q('skills', 'How does Mining work?',
  'Tap a copper or tin rock with a pickaxe in your bag. Rocks empty for a moment and come back. Copper Hills near Diamond Hands has plenty of rocks.',
  ['How do I mine?', 'Where do I find ore?'], vp='mine ore', np='Mining', k='mining ore rock pickaxe copper tin')
q('skills', 'How does Smithing work?',
  'Smelt ore into bars at a forge (every town has one), then smith bars into tools and weapons. Bronze needs copper and tin.',
  ['How do I make a bronze bar?', 'Where is the forge?'], vp='smith', np='Smithing', k='smithing forge bars smelt')
q('skills', 'How does Kindling work?',
  'Kindling is the fire skill. Tap logs in your bag and choose Light (you need the tinderbox). Fires cook food, and the Frozen Shibe skilling boss is all about keeping a brazier burning.',
  ['How do I light a fire?', 'What is Kindling?'], vp='light a fire', np='Kindling', k='kindling fire light tinderbox')
q('skills', 'How does Agility work?',
  'Agility comes from running and moving around the world and from the Grand Tour quest. Higher Agility helps you get around and counts toward your combat level.',
  ['How do I train Agility?'], np='Agility', k='agility run')
q('skills', 'How does Prayer work?',
  'Bury bones from kills for Prayer XP. Prayers help in combat and use Prayer points; pray at an altar to restore them.',
  ['How do I train Prayer?', 'What do bones do?'], vp='train Prayer', np='Prayer', k='prayer bones altar points')
q('skills', 'How does Farming work?',
  'Buy seeds at the general store and plant them in an allotment patch (Wow Landing has them). Come back later to harvest potatoes, onions, cabbages and tomatoes.',
  ['How do I farm?', 'Where do I plant seeds?'], vp='farm', np='Farming', k='farming seeds allotment plant harvest')
q('skills', 'How does Construction work?',
  'Turn logs into planks at the sawmill in the Castle Gigachad courtyard (a small fee per plank), then build with them. More to build comes with the updates.',
  ['How do I get planks?', 'What is Construction?'], vp='get planks', np='Construction', k='construction planks sawmill build')
q('skills', 'How does the Bounty skill work?',
  'Bounty is the slayer skill. Bounty Boss Bonkwell in Wow Landing gives you a bounty: kill a set number of one meme monster. Each kill pays Bounty XP equal to its hitpoints plus Bounty points. Do not like a bounty? Spend 25 points to skip it.',
  ['What is slayer in MemeCapes?', 'Who gives bounties?', 'How do I skip a bounty?'], np='Bounty', k='bounty slayer bonkwell task skip')
q('skills', 'How does the Health skill work?',
  'Health levels raise your hitpoints. It trains alongside your fighting skills, and food heals you back up to the maximum.',
  ['How do I get more hitpoints?'], np='Health', k='health hitpoints hp')
q('skills', 'What are XP lamps?',
  'Items you rub for a lump of XP: the Wish lamp, Big wish lamp and the Genie lamp from the Lamp Genie random event, which lets you pick the skill.',
  ['What is a wish lamp?', 'How do I use a genie lamp?'], np='XP lamps', k='lamp xp wish genie')
q('skills', 'What is my combat level?',
  'A single number that sums up your fighting skills (Attack, Strength, Defence, Health, with a little from Prayer and Agility). It shows on your name tag.',
  ['How is combat level worked out?'], np='the combat level', k='combat level')
q('skills', 'What are the Capes of Accomplishment?',
  'The skill capes: one per skill, sold by the Cape merchant once you reach level 100 in that skill, for a million Meme Coins each. Two skills at 100 and they come trimmed in gold.',
  ['How do I get a skill cape?', 'What is a trimmed cape?'], np='skill capes', k='skill cape accomplishment trimmed')
q('skills', 'Where are the leaderboards?',
  'In the game menu. They rank real players by skill and total level; bots are never on them.',
  ['Is there a hiscores page?', 'How do I see rankings?'], np='the leaderboards', k='leaderboard hiscores ranking')
q('skills', 'What are town tasks and achievement diaries?',
  'Each town has a diary of tasks (chop here, fish there, beat this, visit that). Finishing a diary earns a diary cape. Wow Landing has the easiest one, a good first goal.',
  ['What is an achievement diary?', 'How do I get a diary cape?'], np='achievement diaries', k='diary town tasks achievements')
q('skills', 'What is the loot log?',
  'A collection log of every drop you have found, with the rare ones marked. Filling it earns a Collection cape.',
  ['Collection log', 'How do I track rare drops?'], np='the loot log', k='loot log collection')

# ---------------------------------------------------------------- combat and monsters
q('combat', 'How does combat work?',
  'Classic tick-based combat: tap a monster to attack it and your character trades hits until one of you drops. Your weapon, Attack, Strength and Defence levels decide how often and how hard you hit. Eat food from your bag when your health gets low.',
  ['How do I fight?', 'How do I attack a monster?'], vp='fight', np='combat', k='combat fight attack tick', top=True)
q('combat', 'What happens when I die?',
  'You keep your three most valuable items. The rest go into a gravestone where you died, and you have 15 minutes to walk back and collect them. Items dropped in the Wildlands are lost. You respawn at the castle.',
  ['Do I lose my items when I die?', 'Where do I respawn?', 'What is the gravestone?'], np='dying', k='die death gravestone lose items respawn', top=True)
q('combat', 'How do I heal?',
  'Eat food from your bag: bread heals 5, cooked shrimps 3, party cake 8, potions 10. Health also comes back slowly on its own.',
  ['How do I get my health back?', 'What food heals the most?'], vp='heal', k='heal food eat health')
q('combat', 'Which monsters attack on sight?',
  'Aggressive memes like Bonk, Fartcoin, Book of Meme, Floki, Popcat, Nutty, Mog, Rage Goblins and Doomscrollers attack when you come near. Peaceful ones like the Wojak Wanderer, Slerf, the Ghost of Rugmoon, Vibe Dog and Gigachad only fight back. The NPCs page lists every monster with its style.',
  ['Why does that monster keep attacking me?', 'Which memes are safe?'], np='aggressive monsters', k='aggressive attack on sight peaceful')
q('combat', 'Why are monster levels so strange?',
  'Meme-coin monsters take their level from the real market cap of the coin they parody, so Shibe is level 50 and Slerf is level 1. Story monsters have fixed levels.',
  ['How are monster levels decided?', 'Why is Gigachad only level 5?'], np='monster levels', k='monster level market cap')
q('combat', 'What is the easiest monster?',
  'The level 1 Wojak Wanderer in the fields outside Castle Gigachad. He only fights back, has 5 hitpoints, and drops Meme Coins, bread and meme scraps.',
  ['Which monster should I fight first?', 'Where are low level monsters?'], np='the easiest monster', k='easy first monster wojak level 1')
q('combat', 'Where is Bonk?',
  'In his forest. Bonk is a level 25 boss with 28 hitpoints who attacks on sight and drops the Bonk bat as a rare. His little cousins, the Bonk Hounds, are level 5 and needed for The Bonk Problem quest.',
  ['How do I beat Bonk?', 'What does Bonk drop?'], np='Bonk', k='bonk forest boss bat')
q('combat', 'Who is the Ratio Lord?',
  'A level 75 boss with 175 hitpoints waiting in his lair in the far north-west. The Ratio Lord quest (after The Bonk Problem and Wojak Blues) sends you there; he drops Ratio shards and, rarely, Ratio Knight armour and the Ratio shield.',
  ['How do I beat the Ratio Lord?', 'Where is the Ratio Lord lair?'], np='the Ratio Lord', k='ratio lord boss lair')
q('combat', 'What is the Frozen Shibe?',
  'A skilling boss on the frozen peak north of the castle. Nobody fights him with swords: you chop frost roots and burn them in the brazier (Kindling level 10) until the ice gives up, and he pays in supply crates full of loot.',
  ['How do I fight the Frozen Shibe?'], np='the Frozen Shibe', k='frozen shibe skilling boss brazier')
q('combat', 'What are special attacks?',
  'Some weapons have a special attack that uses your special energy for a bigger hit or an effect. The bar refills over time.',
  ['How do I use a special attack?'], np='special attacks', k='special attack spec energy')
q('combat', 'What do prayers do?',
  'Prayers boost you in a fight while they drain Prayer points. Restore points at an altar, and raise your Prayer level by burying bones.',
  ['How do I use prayers?'], np='prayers', k='prayer boost altar')
q('combat', 'What is the Wildlands?',
  'The dangerous land out past Rugpull Ridge where Algorithm Cultists roam. Items you drop by dying there are lost for good, so go in light.',
  ['Where is the Wildlands?', 'Is the Wildlands dangerous?'], np='the Wildlands', k='wildlands dangerous lost items')
q('combat', 'What are rare drops?',
  'Most monsters have a rare drop with the odds shown on the NPCs page: the Bonk bat from Bonk, the Viking helmet from Floki, Mog shades from Mog Coin, the Wojak mask, the Rage mask, the Jester hat, Chad armour and more. The loot log keeps track of what you have found.',
  ['What is the rarest drop?', 'Drop rates'], np='rare drops', k='rare drop rates loot')
q('combat', 'Can I get a pet?',
  'Yes. Bonk Hounds and Golden Hounds have a 1 in 100 chance to drop a pup that follows you around. Pets are for show only.',
  ['How do I get a pet?', 'What pets are there?'], np='pets', k='pet pup hound')
q('combat', 'What are the random events?',
  'Every 25 to 45 minutes someone may pop in: Rich Wojak leaves Meme Coins, Snack Shibe brings free food and the Lamp Genie grants an XP lamp. Each has a 1 in 200 chance of leaving a rare cape.',
  ['Who is Rich Wojak?', 'Who is the Snack Shibe?', 'What is the Lamp Genie?'], np='random events', k='random event rich wojak snack shibe genie')
q('combat', 'What is a Clout Bandit?',
  'A level 20 thief who steals Meme Coins straight out of your bag mid-fight. Kill him fast, and bank your coins before you go looking for him.',
  ['Why did I lose coins in a fight?'], np='the Clout Bandit', k='clout bandit steal coins')
q('combat', 'What are the Meme Caves?',
  'A combat challenge near Moon Landing. Beat it and you earn the Meme cape.',
  ['How do I get the Meme cape?'], np='the Meme Caves', k='meme caves challenge cape')
q('combat', 'Why can\'t I hit anything?',
  'Low Attack level against a high-defence monster means lots of misses. Train on weaker memes first, use the best sword you can smith or find, and keep your health up with food.',
  ['I keep missing', 'Why do I do so little damage?'], np='missing hits', k='miss damage low hit')
q('combat', 'Can other players attack me?',
  'No. There is no player-versus-player fighting in the world. Meme Wars, a team minigame, is planned for a later update.',
  ['Is there PvP?', 'Can I fight other players?'], np='PvP', k='pvp player versus attack')
q('combat', 'What is the Bot Captain?',
  'The boss of the Feels Bad, Man quest: he and his Spam Bots attack the castle gate and you hold it. Nothing to do with the computer-controlled characters that walk the world.',
  ['Who attacks the castle gate?'], np='the Bot Captain', k='bot captain spam bots gate quest')

# ---------------------------------------------------------------- items, bag and bank
q('items', 'How big is my bag?',
  'Thirty-five slots. Meme Coins do not take a slot. Bank the rest at any bank to make room.',
  ['How many items can I carry?', 'Inventory size', 'My bag is full'], np='the bag', k='bag inventory slots full', top=True)
q('items', 'How does the bank work?',
  'Every town has a bank and the castle has one too. Tap the banker to deposit and withdraw items; the bank has tabs and a search box, shows a picture of everything, and keeps your items safe even when you die. Bank booths in the field work the same.',
  ['Where is the bank?', 'How do I deposit items?', 'Is the bank shared between towns?'], np='the bank', k='bank deposit withdraw tabs search', top=True)
q('items', 'How do I examine an item?',
  'Tap and hold (or right-click) an item in your bag and choose Examine. Every item has a line of its own, and the Items page on the site lists them all.',
  ['What does this item do?', 'How do I see item info?'], vp='examine an item', k='examine item info')
q('items', 'How do I drop an item?',
  'Tap and hold the item in your bag and choose Drop. Dropped items vanish after a while, so bank anything you want to keep.',
  ['Can I throw items away?'], vp='drop an item', k='drop item discard')
q('items', 'How do I equip a weapon or armour?',
  'Tap the item in your bag and choose Wear or Wield. Weapons, helmets, body armour, shields, necklaces and capes all have a slot and show on your character in 3D.',
  ['How do I wear armour?', 'How do I wield a sword?'], vp='equip an item', k='equip wear wield armour weapon')
q('items', 'What is a teleport tablet?',
  'A one-use tablet sold in general stores. Break it to jump straight to Wow Landing, Stonks City or Froggo\'s Pond.',
  ['How do teleport tablets work?'], np='teleport tablets', k='teleport tablet break')
q('items', 'What are meme scraps for?',
  'Bits of old memes dropped by many monsters. They are collectables and sell to shops; keep an eye on the quests and the loot log for uses.',
  ['What do I do with meme scraps?'], np='meme scraps', k='meme scrap use')
q('items', 'What is a meme hunt?',
  'A treasure trail. Read the clue scroll, follow it across the world, and dig or search where it says. Finishing one can pay a Treasure cape or a Gilded meme hat.',
  ['How do treasure trails work?', 'I found a clue scroll'], np='meme hunts', k='meme hunt clue scroll treasure trail')
q('items', 'What is a strongbox?',
  'A locked box of loot. Open it from your bag and hope for treasure. Supply crates from the Frozen Shibe work the same way.',
  ['How do I open a strongbox?'], np='strongboxes', k='strongbox crate loot open')
q('items', 'Where do I get a better axe or pickaxe?',
  'Smith one from iron at a forge, buy one at the general store, or earn one: Wojak Blues rewards an iron axe.',
  ['How do I get an iron axe?'], vp='get a better axe', k='iron axe pickaxe better upgrade')
q('items', 'Where do I buy food?',
  'The general store in every town sells food, tools, seeds and teleport tablets, and buys most things from you. Bread, cooked fish and party cake are the easy heals.',
  ['What does the general store sell?', 'Where is the shop in town?'], np='the general store', k='general store shop buy food sell')
q('items', 'Do items have stats?',
  'Weapons and armour do. Capes are cosmetic except the Burn and Rug Pit capes, which come later. Skins never change stats.',
  ['Which items give bonuses?'], np='item stats', k='stats bonus items')
q('items', 'What are star shards?',
  'Dust from a shooting star. Shops buy them. Look up when a star falls.',
  [], np='star shards', k='star shards shooting')
q('items', 'Can I lose items from my bank?',
  'No. The bank keeps everything safe through deaths and disconnects. Only what is in your bag can be lost when you die.',
  ['Is the bank safe?'], np='bank safety', k='bank safe lose')
q('items', 'How do I get more Meme Coins?',
  'Drops from monsters, quest rewards, selling logs, fish, ore and bars to the general store or the Stock Market, Rich Wojak visits, and the starter guide. Bank them so a Clout Bandit cannot pick your pocket.',
  ['Fastest way to make money', 'How do I earn coins?'], vp='earn Meme Coins', k='money coins earn fast')

# ---------------------------------------------------------------- towns and travel
q('world', 'What towns are there?',
  'Eight meme towns plus Castle Gigachad: Wow Landing, Froggo\'s Pond, Stonks City, Diamond Hands, Rugpull Ridge, HODL Heights, Moon Landing and Chad Falls. Every town has a bank, a general store, a forge and a cooking range, a well, stalls, lamps and a Meme Telly ring.',
  ['How many towns are there?', 'List of towns'], np='the towns', k='towns list eight', top=True)
q('world', 'Where is the first town?',
  'Wow Landing, down the road from the castle. Thatched cottages, a windmill, the church, allotments, Bounty Boss Bonkwell by the forge and the easiest achievement diary in the game.',
  ['Where is Wow Landing?', 'What is in Wow Landing?'], np='Wow Landing', k='wow landing first town')
q('world', 'What is Froggo\'s Pond?',
  'A swamp town east of the castle built on stilts over the water, with fish shacks, docks, lily pads, a shrine and fishing spots right off the boardwalks. The wild Froggo roams nearby and is not polite.',
  [], np="Froggo's Pond", k='froggo pond swamp fishing')
q('world', 'What is Stonks City?',
  'The money town in the middle of the map where every road crosses: gothic row houses, the old Exchange and the clock tower. It rains there more than it should.',
  [], np='Stonks City', k='stonks city exchange')
q('world', 'What is Diamond Hands?',
  'Blue-and-white manor houses in the north-west, home of the knights who never sell. Copper Hills and its mines are a short walk away.',
  [], np='Diamond Hands', k='diamond hands town copper hills')
q('world', 'What is Rugpull Ridge?',
  'The south-west frontier: boarded-up houses, the manor, the crypt, dead trees, and the Wildlands and the Ratio Lord\'s lair beyond.',
  [], np='Rugpull Ridge', k='rugpull ridge graveyard')
q('world', 'What is HODL Heights?',
  'High in the north under the Copium Mountains: log cabins, the lodge, the monastery, the bell tower and snow.',
  [], np='HODL Heights', k='hodl heights snow north')
q('world', 'What is Moon Landing?',
  'The south-east, where the moon memes landed: habitat pods, the dome, the antenna, the lunar lander and craters. The Meme Caves open nearby.',
  [], np='Moon Landing', k='moon landing south east')
q('world', 'What is Chad Falls?',
  'Red-roofed villas on the east coast by the sea, with the colosseum and the baths. The last stop on the Grand Tour.',
  [], np='Chad Falls', k='chad falls coast')
q('world', 'How do I travel between towns?',
  'Walk the roads (signposts at every town entrance point the way), break a teleport tablet, or step into a Meme Telly ring to jump to any town you have visited before.',
  ['How do I get to another town?', 'Fast travel'], vp='travel between towns', k='travel roads teleport telly')
q('world', 'Is there a map?',
  'Yes, the World map in the game menu shows the towns, roads and your position. A better minimap with fog of war and waypoints is on the roadmap.',
  ['How do I open the map?', 'Where am I?'], np='the map', k='map minimap world')
q('world', 'What is the Grand Tour?',
  'A quest from Froggo: walk to all eight towns in order, easiest first. Each town you reach joins the Meme Telly, and the reward is Agility XP, Meme Coins and a Big wish lamp.',
  [], np='the Grand Tour', k='grand tour quest towns telly')
q('world', 'What are Wall St., Ember Coast, the Trenches and Normie Island?',
  'New land that is on the map now and gets its buildings with the updates: Wall St. for player-to-player trading, Ember Coast with its volcano and lava zone, the Trenches for Survive the Trenches, and Normie Island, the tutorial island new players will start on.',
  ['What is Wall St.?', 'Where is the lava zone?', 'What is Normie Island?'], np='the new regions', k='wall st ember coast trenches normie island new land')
q('world', 'Does the game have day and night?',
  'Yes. The sun moves, lamps light the streets at night, shadows follow the sun and it rains now and then. Nothing in the game needs a particular time of day.',
  ['Why is it dark?', 'Why is it raining?'], np='day and night', k='night dark rain weather day')
q('world', 'Can I enter the buildings?',
  'Banks, shops, forges and ranges are used from outside by tapping the person or the counter. Houses are scenery for now.',
  ['Why can\'t I go inside houses?'], vp='enter buildings', k='enter inside buildings houses')
q('world', 'How big is the world?',
  'A castle, eight towns, forests, a river with bridges, mountains, a swamp, a coast and the new regions in the east and south. The map grows with every update.',
  ['How large is the map?'], np='the size of the world', k='world size map big')

# ---------------------------------------------------------------- quests
q('quests', 'How do quests work?',
  'Froggo by the castle gate hands out most quests (a gold ! over his head means he has one). Do the task, walk back, claim the reward. Quests give quest points, and once every quest is done the Cape merchant sells the Quest cape.',
  ['Where do I get quests?', 'How do I start a quest?'], np='quests', k='quests froggo start reward', top=True)
q('quests', 'How many quests are there?',
  'Ten so far: Proof of Work, The Bonk Problem, Wojak Blues, The Ratio Lord, The Grand Tour, and Chapter 1, The Great Rug: Much Wow Such Cake, Wallet Not Found, Touch Grass, The Fish Are Rugged and Feels Bad, Man. More chapters come with the updates.',
  ['List of quests'], np='the quest list', k='quests list how many')
q('quests', 'What is Proof of Work?',
  'The first quest: defeat 3 memes of any kind. Rewards Attack XP, Meme Coins, a party cake and 1 quest point.',
  [], np='Proof of Work', k='proof of work quest first')
q('quests', 'What is The Bonk Problem?',
  'Defeat 3 Bonk Hounds (level 5) before they bonk the kingdom. Needs Proof of Work. Rewards Strength XP, Meme Coins, a potion and 1 quest point.',
  [], np='The Bonk Problem', k='bonk problem quest hounds')
q('quests', 'What is Wojak Blues?',
  'Defeat 5 Wojak Wanderers. Needs Proof of Work. Rewards Defence XP, Meme Coins, an iron axe and 1 quest point.',
  [], np='Wojak Blues', k='wojak blues quest')
q('quests', 'What is The Ratio Lord quest?',
  'Defeat the level 75 Ratio Lord in his lair in the far north-west (check the world map). Needs The Bonk Problem and Wojak Blues. Rewards a lot of Attack XP, Meme Coins, the Ratio Blade and 5 quest points.',
  [], np='the Ratio Lord quest', k='ratio lord quest blade')
q('quests', 'What is Much Wow, Such Cake?',
  'Chef Bagholder bought every ingredient at the top: bring him an egg, a bucket of milk and a pot of flour from Wow Landing. Rewards Cooking XP, Meme Coins, a party cake and 1 quest point.',
  [], np='Much Wow Such Cake', k='much wow cake quest chef bagholder')
q('quests', 'What is Wallet Not Found?',
  'Froggo explains the Great Rug and three forgetful Wojaks each remember one word of your seed phrase (a story item, not a real one). Needs Much Wow, Such Cake. Rewards an XP lamp, Meme Coins and a Seed phrase scroll.',
  [], np='Wallet Not Found', k='wallet not found quest seed phrase scroll')
q('quests', 'What is Touch Grass?',
  'Farmer Ted\'s allotments are full of Doomscrollers: plant a potato and tell each one to go outside. Rewards Farming XP, Meme Coins and 1 quest point.',
  [], np='Touch Grass', k='touch grass quest farmer ted doomscroller')
q('quests', 'What is The Fish Are Rugged?',
  'Fisherwoman Nemo\'s pond keeps draining: search the muddy shallows and find out where the Liquidity goes. Needs Fishing level 5. Rewards Fishing XP, Meme Coins and a meme hunt scroll.',
  [], np='The Fish Are Rugged', k='fish rugged quest nemo')
q('quests', 'What is Feels Bad, Man?',
  'The Bot Captain and his Spam Bots attack the castle gate: hold it. Needs the four Chapter 1 quests and Proof of Work. Rewards combat XP, Meme Coins, the first Cape fragment and 2 quest points.',
  [], np='Feels Bad Man', k='feels bad man quest bot captain gate')
q('quests', 'What are quest points?',
  'Each quest gives points; they show on your profile and all of them together unlock the Quest cape at the Cape merchant.',
  [], np='quest points', k='quest points')
q('quests', 'I finished the task but the quest did not complete',
  'Walk back to the quest giver (usually Froggo at the castle gate) and talk to them to hand it in. If the quest still shows as unfinished, check the exact count: the quest card says how many are left.',
  ['My quest is stuck', 'Quest not completing'], np='a stuck quest', k='quest stuck not complete hand in')
q('quests', 'What is a Cape fragment?',
  'A piece of one of the OG Capes. The story chapters hand them out as you free the Originals\' capes from the Rugpuller.',
  [], np='Cape fragments', k='cape fragment feels')

# ---------------------------------------------------------------- capes
q('capes', 'What is the MemeCape?',
  'The rarest thing in the game: every meme, one cape, one crown, worn in 3D with the hood and crown over your head. The Cape merchant in the castle courtyard sells it for 100,000,000 Meme Coins, earned in play. Nobody can buy it with real money.',
  ['How do I get the MemeCape?', 'How much is the MemeCape?'], np='the MemeCape', k='memecape crown rarest', top=True)
q('capes', 'What is the Quest cape?',
  'The MemeCape without the hood and crown, for finishing every quest. The Cape merchant sells it for 100,000 Meme Coins once all quests are done.',
  ['How do I get the Quest cape?'], np='the Quest cape', k='quest cape')
q('capes', 'What kinds of capes are there?',
  'Vibe Capes (12 colours, bought with Meme Coins), Skill Capes at level 100, Diary and Collection capes, War Capes, the Burn Cape, the Rug Pit Cape, Quest Capes, the seven OG story capes, Genesis Capes and Sponsor Capes. Only the Burn and Rug Pit capes have combat stats, so a bought cape never beats an earned one in a fight.',
  ['List of capes', 'Which capes have stats?'], np='the cape types', k='capes list types stats')
q('capes', 'Can I buy a cape with real money?',
  'The capes that mean something are earned or bought with Meme Coins inside the game. A custom cape with your own design can be ordered in the Shop, but it is cosmetic only and marked as a custom. Genesis Capes come with $CAPES after the token and are cosmetic too.',
  ['Can I pay for the MemeCape?'], vp='buy a cape', k='buy cape real money')
q('capes', 'What are Genesis Capes?',
  'Limited runs of 100 per design, minted on Solana as cosmetics only, bought with $CAPES (60% of each purchase is burned) or earned free by the top 10 on each monthly hiscore. They arrive after the token, not before.',
  ['What are the NFT capes?'], np='Genesis Capes', k='genesis capes nft limited')
q('capes', 'What is the Cape Rack?',
  'Your collection of capes, shown on your profile and in the game. Every cape you have earned or bought hangs there.',
  [], np='the Cape Rack', k='cape rack collection profile')
q('capes', 'What is the Chad cape?',
  'A rare drop from Chad Brutes (1 in 125). Flowing with confidence.',
  [], np='the Chad cape', k='chad cape drop')
q('capes', 'What are OG Capes?',
  'The seven story capes of the Originals: Much, Feels, Doomer, Based, Up-Only, Wen and Rug. They are won through the story chapters and can never be traded.',
  [], np='OG Capes', k='og capes story')
q('capes', 'What are Sponsor Capes?',
  'Meme-coin communities can put their mascot on a cape through the Shop; holders of that project claim it in-game. Cosmetic only.',
  [], np='Sponsor Capes', k='sponsor capes community')
q('capes', 'Where is the Cape merchant?',
  'In the Castle Gigachad courtyard, with a very full cape rack. He sells skill capes at level 100, the Quest cape, and the MemeCape itself.',
  [], np='the Cape merchant', k='cape merchant courtyard')

# ---------------------------------------------------------------- Meme Coins and $CAPES
q('coins', 'What are Meme Coins?',
  'The in-game money. You earn them from drops, quests, skilling and selling to shops, and spend them at shops, the Cape merchant and the Stock Market. They are not a token and have no cash value.',
  ['Are Meme Coins real money?'], np='Meme Coins', k='meme coins currency money', top=True)
q('coins', 'Is there a $CAPES token?',
  'Not yet. MemeCapes launches as a free game first. When the token exists, the contract address will be posted only on memecapes.com and on @Mrsnakebaby on X. Anything using the name before that is fake: do not buy it.',
  ['Where do I buy $CAPES?', 'What is the contract address?', 'Is $CAPES out?'], np='the $CAPES token', k='token capes contract address buy fake', top=True)
q('coins', 'How does the $CAPES exchange work?',
  'At any bank you will be able to exchange Meme Coins for $CAPES, starting at 100 Meme Coins per $CAPES, at most 100 $CAPES a day per player. The rate steepens as the player pot drains so it lasts for years. The exchange opens once the public pot wallet is funded, after the token launches.',
  ['How do I turn Meme Coins into $CAPES?', 'What is the exchange rate?', 'What is the daily cap?'], np='the exchange', k='exchange rate cap 100 day pot')
q('coins', 'What do $CAPES holders get?',
  'In-game perks only. Link a wallet at any bank by signing a free message (nothing moves, no seed phrase). Hold 1% of all $CAPES and you get Cape Club free plus a free skin every 14 days; hold 0.1% for 30 days and you can take each month\'s Skin of the Month free; hold 3% for 14 days and your project can run a free partner ad in the towns. Holding pays no money and no tokens, and it is not an investment.',
  ['What are the holder perks?', 'What is Cape Club?', 'Do holders earn anything?'], np='holder perks', k='holders perks cape club skin partner ad link wallet')
q('coins', 'How do I link my wallet?',
  'Talk to any banker and choose link wallet. Your wallet app asks you to sign a short message that proves the wallet is yours. It is not a transaction: nothing is sent, nothing is approved, and we never ask for your seed phrase. The game checks the balance on the blockchain every day.',
  ['Is linking a wallet safe?', 'Does linking cost anything?'], vp='link my wallet', k='link wallet sign message bank')
q('coins', 'Does MemeCapes hold my crypto?',
  'Never. Every payment goes straight from your wallet to the address shown, and you see the exact transfer in your wallet before you approve it. MemeCapes has no access to your wallet, keys or funds.',
  ['Is my wallet safe with MemeCapes?', 'Do you have custody of my funds?'], np='custody', k='custody hold crypto wallet safe')
q('coins', 'Will $CAPES go up?',
  'Nobody knows, and we will not guess. $CAPES is a fun token for use with the game, not an investment, and crypto can go to zero. Only ever spend what you are happy to lose. Nothing on this site is financial advice.',
  ['Is $CAPES a good investment?', 'Price prediction', 'Should I buy $CAPES?'], np='the $CAPES price', k='price investment prediction moon')
q('coins', 'Is there staking or revenue share?',
  'No staking yield and no revenue share. The launchpad\'s creator fees go to the creator, not to holders. The token is a cape you can trade, not a security.',
  ['Do holders get a cut of revenue?', 'Can I stake $CAPES?'], np='staking', k='staking yield revenue share')
q('coins', 'How is $CAPES distributed?',
  'On a public bonding curve, with nothing allocated in advance. In the transaction that creates the coin the creator buys 20%: half is burned on the spot (the supply drops to 900 million) and half goes into Jupiter Lock right after, opening 1/24 a month for 24 months, with no way to cancel it; the player pot is funded over time in a public ecosystem wallet with every addition posted; marketing and payments wallets hold no tokens. The $CAPES page has the table.',
  ['What is the tokenomics?', 'Is there a presale?', 'How much does the team hold?'], np='the tokenomics', k='tokenomics supply allocation presale team')
q('coins', 'What burns $CAPES?',
  'Play, not promises: limited cosmetics bought with $CAPES (60% burned), a small tax on player trades once they open, sponsored monsters (half burned), and the launchpad (half of what MemeCapes earns buys $CAPES and burns it). Burns are posted on-chain.',
  ['Is $CAPES deflationary?', 'How do burns work?'], np='burns', k='burn deflation')
q('coins', 'Can I withdraw Meme Coins as real money?',
  'No. Meme Coins are game content with no cash value and cannot be redeemed for money from us. The only bridge is the in-game exchange to $CAPES, after the token launches, within the daily cap.',
  ['Can I cash out?', 'Sell Meme Coins for cash'], vp='cash out', k='cash out withdraw real money')
q('coins', 'Why is the exchange closed?',
  'It opens once the token has launched and the public player pot wallet is funded. Until then the banker shows the note and your Meme Coins keep piling up.',
  ['When does the exchange open?'], np='the closed exchange', k='exchange closed open')
q('coins', 'Can I buy Meme Coins with real money?',
  'No. Meme Coins are earned in play only. Buying or selling them for real money outside the game is against the rules.',
  ['Buy gold', 'Can I pay for coins?'], vp='buy Meme Coins', k='buy meme coins real money gold')

# ---------------------------------------------------------------- skins and the Wardrobe
q('skins', 'What are skins?',
  'New looks for a cape pattern or a weapon type. They only change how things look, never stats. Open the Wardrobe in the game to see every skin with a picture and try it on for 30 seconds before you decide.',
  ['What is the Wardrobe?', 'Do skins give bonuses?'], np='skins', k='skins wardrobe cosmetic', top=True)
q('skins', 'What is the Skin of the Month?',
  'Each month a new skin comes out. A wallet linked to your account that has held at least 0.1% of all $CAPES for 30 days can take it free at any bank or in the Wardrobe, once per account. Everyone else can buy it in the skin store, and it stays in the store after its month. Once you have a skin it is yours for good.',
  ['How do I get the monthly skin?', 'Is the Skin of the Month free?'], np='the Skin of the Month', k='skin of the month monthly free')
q('skins', 'How do I buy a skin?',
  'Open the Wardrobe, tap the skin to see the big picture, try it on, then choose Buy. Skins are paid from your wallet and belong to your account from then on.',
  ['Where is the skin store?'], vp='buy a skin', k='buy skin store')
q('skins', 'Can I trade or sell a skin?',
  'No. Skins belong to your account and cannot be traded, sold or given away. That keeps holder perks in-game and stops farming.',
  ['Are skins tradeable?'], vp='trade a skin', k='trade sell skin account bound')
q('skins', 'How does try it on work?',
  'Tap a skin in the Wardrobe and choose Try it on: the camera circles your character wearing it for 30 seconds, then everything goes back to normal.',
  ['Can I preview a skin?'], vp='try a skin on', k='try on preview skin')
q('skins', 'Do I keep a skin after its month?',
  'Yes, for good. Skins never expire, and past months stay in the store.',
  [], np='keeping skins', k='keep skin expire')
q('skins', 'Can I get a refund on a skin?',
  'Skins are delivered at once and are not refundable, except where the law requires otherwise. Use Try it on before buying.',
  ['Refund a skin'], np='skin refunds', k='refund skin')
q('skins', 'Can I wear a cape skin without a cape?',
  'Cape skins change the look of a cape you wear. Try it on shows the cape even if you are not wearing one yet.',
  [], np='cape skins', k='cape skin wear')

# ---------------------------------------------------------------- trading and the Stock Market
q('trade', 'How do I trade with another player?',
  'Type /trade and their name, or tap them and choose Trade. Both of you put items in the window, check the big pictures, names and values, then press Accept on both screens. Watch for the change warnings: if the other side changes anything, the accepts reset.',
  ['How does player trading work?', 'Trade request'], vp='trade with a player', np='player trading', k='trade player window accept', top=True)
q('trade', 'Why did my trade request go nowhere?',
  'The other player may be busy, offline, ignoring requests, or a bot: bots never trade. Try someone else or ask in chat.',
  ['Trade request sent but nothing happened'], np='an unanswered trade request', k='trade request nothing bot')
q('trade', 'Can I get scammed in a trade?',
  'The trade window is built to make it hard: both players see the same items with pictures and values, a change by either side cancels the accepts, and nothing moves until both press Accept twice. Still, read the window every time and never trade for anything promised outside the window.',
  ['Is trading safe?', 'Trade scam'], np='trade safety', k='scam trade safe')
q('trade', 'What is the Stock Market?',
  'The Stock Market Broker in the castle courtyard buys and sells food, logs, planks, ores, bars, gems, potions, seeds and more. Prices drift with what people buy and sell, every sale pays a 2% tax, and buy limits reset every four hours. Player-to-player offers arrive when the market moves to Wall St.',
  ['Where is the Stock Market?', 'How do I sell to the broker?'], np='the Stock Market', k='stock market broker sell buy tax limits')
q('trade', 'What is Diamond Hands mode?',
  'A mode you can switch on for your account that turns off trading and the Stock Market, for players who want to earn everything themselves. It is your choice.',
  ['Can I play ironman?', 'How do I turn off trading?'], np='Diamond Hands mode', k='diamond hands mode ironman no trading')
q('trade', 'What can I trade?',
  'Items and Meme Coins. Skins, capes you earned, OG capes and quest rewards that are account-bound cannot be traded.',
  ['Which items are untradeable?'], np='tradeable items', k='trade items untradeable bound')
q('trade', 'The trade window closed by itself',
  'A trade closes when either player walks away, cancels or loses connection. If both seals were already pressed, your bag updates when you reconnect; otherwise nothing was swapped.',
  ['My trade got cancelled'], np='a closed trade', k='trade closed cancelled')
q('trade', 'Can I sell items to other players for real money?',
  'No. Selling accounts, items or Meme Coins for real money outside the official shop is against the rules and can get accounts banned.',
  ['Real world trading'], np='real-money trading', k='rwt real money sell account ban')

# ---------------------------------------------------------------- the shop
q('shop', 'What does the Shop sell?',
  'Town billboards (your banner in a meme town for a week), sponsored monsters (your community\'s mascot roams the world for a month) and custom capes and items (one of a kind, your design, worn in 3D, cosmetic only). Paid with SOL, USDC or $CAPES from your own wallet.',
  ['What can I buy in the shop?', 'How do I put my project in the game?'], np='the Shop', k='shop billboard sponsored monster custom cape', top=True)
q('shop', 'How does buying in the Shop work?',
  'Send the exact amount from your wallet to the MemeCapes address shown on the Shop page, paste the transaction so the page can confirm it on the blockchain, then send your order and design. Capes and items come as a code you redeem at any bank in the game.',
  ['How do I pay in the shop?', 'How do I redeem a code?'], vp='buy from the Shop', k='shop pay transaction code redeem')
q('shop', 'Can I get a refund from the Shop?',
  'If we refuse an order before delivering it, we refund the amount in the same currency to the wallet it came from, minus network fees. Once a code, cape, item or ad has been delivered the purchase is final, except where the law requires otherwise.',
  ['Refund policy'], np='shop refunds', k='refund shop policy')
q('shop', 'Do custom capes give an advantage?',
  'No. Custom capes and items are cosmetic only and give no combat advantage. They remain game content like everything else.',
  ['Are shop items pay to win?'], np='pay to win', k='pay to win advantage cosmetic')
q('shop', 'What are the rules for ads and designs?',
  'Your design must be your own work or something you have the right to use, and it must follow the rules: nothing illegal, hateful, sexual, violent or infringing. Every design is reviewed by hand and we can refuse any order.',
  ['Can I advertise my token?'], np='ad rules', k='ad rules design review refuse')
q('shop', 'What is a burn ad?',
  'A website ad for projects that burn $CAPES: send the ad first, and only after it is approved do you burn the amount shown with a real burn. Approved ads share the ad spot on the home page, with odds based on how much each project burned. Burns are final.',
  ['How do I get an ad on the home page?'], np='burn ads', k='burn ad home page')
q('shop', 'What happens if the game is down during my ad?',
  'If the game is down for more than 48 hours in a row during your ad or sponsored monster, we extend it by the same amount.',
  [], np='ad downtime', k='ad down extend')
q('shop', 'Is there a partner ad for holders?',
  'A wallet that has held at least 3% of all $CAPES for 14 days can run a free partner ad: a billboard and an NPC in every meme town plus a cape colour. It is approved by hand and comes down as soon as a check finds the wallet under 3%.',
  [], np='partner ads', k='partner ad holder free')

# ---------------------------------------------------------------- launchpad
q('launch', 'What is the launchpad?',
  'Anyone can launch a Solana coin from memecapes.com. You choose the trading fee and how much of it you keep, bots that buy in the first seconds pay a sniper fee, you can split your share with up to 10 wallets, and the coin\'s liquidity is locked for good when it graduates. Your wallet signs everything; MemeCapes never holds your keys or your money.',
  ['How do I launch a coin?', 'Can I create a token on MemeCapes?'], np='the launchpad', k='launchpad launch coin token create', top=True)
q('launch', 'What does it cost to launch a coin?',
  'The network fees of creating the coin on Solana, paid from your wallet, plus the trading fee you choose for your coin. The Launch page shows every fee before you sign.',
  ['Launch fees'], np='launch fees', k='launch cost fee')
q('launch', 'What is the sniper fee?',
  'Buyers in the first seconds after a launch pay a higher fee that fades quickly. It makes sniping with bots expensive and leaves more of the early supply for real people.',
  [], np='the sniper fee', k='sniper fee bots early')
q('launch', 'What does graduation mean?',
  'When a coin fills its bonding curve it graduates to a normal market, and its liquidity is locked for good: nobody, not the creator and not MemeCapes, can pull it.',
  ['Is the liquidity locked?'], np='graduation', k='graduate liquidity locked')
q('launch', 'Who owns the coins launched here?',
  'The people who launch them. MemeCapes receives a part of each coin\'s trading fee, shown on the coin\'s page before anyone trades, and nothing else. We can hide a coin from our pages if it breaks the rules, but we cannot change or remove it from the blockchain.',
  ['Does MemeCapes endorse the coins?'], np='coin ownership', k='own coin creator endorse')
q('launch', 'Is launching or buying coins risky?',
  'Yes. Most new coins lose most of their value, prices can go to zero, and blockchain transactions cannot be reversed. Nothing on the launchpad is investment advice. Only put in what you are happy to lose.',
  ['Can I lose money on the launchpad?'], np='launchpad risk', k='risk lose money')
q('launch', 'How do I split fees with my team?',
  'When you set up the coin you can name up to 10 wallets and the share each one gets. It is written into the coin and shown on its page.',
  [], vp='split creator fees', k='split fees team wallets')
q('launch', 'What is the launch check?',
  'Every coin page shows who bought in the launch block and the next few, and whether they still hold, so buyers can spot bundling and sniping before they trade.',
  ['How do I spot a bundled launch?'], np='the launch check', k='launch check bundling snipers')
q('launch', 'Can I launch from inside the game?',
  'The Launchpad clerk in Gigachad Town and Stonks City opens the Launch page for you in a new tab.',
  [], np='the Launchpad clerk', k='launchpad clerk in game')
q('launch', 'Why did my launch transaction fail?',
  'Usually not enough SOL for the network fees, a wallet that rejected the signature, or a congested network. Check the wallet, top up a little SOL and try again; nothing is created until the transaction confirms.',
  ['Launch failed'], np='a failed launch', k='launch failed transaction')
q('launch', 'Does the launchpad work on devnet or testnet?',
  'The public launchpad is on Solana mainnet. Test networks are for the team.',
  [], np='devnet', k='devnet testnet')

# ---------------------------------------------------------------- watch and stream
q('stream', 'What is the Watch page?',
  'Every trade, launch and stream as it happens: the wallets winning, the coins they are in, and the people streaming. Watching is free.',
  ['Where can I see live trades?', 'Where do I watch streams?'], np='the Watch page', k='watch live trades streams', top=True)
q('stream', 'How do I stream on MemeCapes?',
  'Buy a streamer pass on the Stream page (a monthly fee paid in SOL from your wallet at the live price), then go live from your browser (camera or screen) or from OBS with your stream key. You can attach a coin you launched so viewers can buy it under your video.',
  ['How do I go live?', 'Can I stream with OBS?'], vp='stream', np='streaming', k='stream go live obs pass', top=True)
q('stream', 'What does streaming cost?',
  'A streamer pass is a fee for 30 days, shown on the Stream page, paid in SOL from your wallet. MemeCapes takes nothing from your tips or subscriptions: 100% goes to you. Small print: the pass covers a set amount of streaming; if your streaming uses more than that, the price may vary.',
  ['How much is the streamer pass?'], np='the streamer pass', k='streamer pass cost month')
q('stream', 'Who gets my tips?',
  'You, all of it. Tips and subscriptions go straight from the viewer\'s wallet to the streamer\'s wallet. MemeCapes never holds them and takes no cut, which also means we cannot refund them: ask the streamer.',
  ['Does MemeCapes take a cut of tips?', 'Can I refund a tip?'], np='tips and subscriptions', k='tips subscriptions cut refund')
q('stream', 'Can I get a refund on a streamer pass?',
  'No. The pass starts the moment the payment confirms and the service is provided from then on, so it is not refundable except where the law requires otherwise.',
  [], np='pass refunds', k='refund streamer pass')
q('stream', 'Do I need to be 18 to stream?',
  'Yes, like everything on MemeCapes. Stream only what is yours to show and follow the rules; we can end streams and hide channels that break them.',
  [], np='stream rules', k='stream 18 rules')
q('stream', 'How do I tip a streamer?',
  'Press Tip under the video and approve the transfer in your wallet. It goes straight to the streamer.',
  [], vp='tip a streamer', k='tip streamer wallet')
q('stream', 'My stream shows offline',
  'Check the pass is active on the Stream page, that OBS is using the current stream key, and give the player a minute after you start. If it still shows offline, stop and start the stream once.',
  ['Stream not showing', 'OBS not connecting'], np='an offline stream', k='stream offline obs key')

# ---------------------------------------------------------------- the AI agent
q('agent', 'What is the AI Agent page?',
  'A live page where an AI boss agent run by the builder posts what it is working on: its crews, their status and a public log. It is a window into how the project is built, not something that touches your account or wallet.',
  ['What is MemeSnake?', 'What does the AI Agent do?'], np='the AI Agent', k='ai agent memesnake live page', top=True)
q('agent', 'Does the AI Agent control my money or wallet?',
  'No. It never has access to player accounts, wallets or funds. Its page only shows its own activity log.',
  ['Is the AI Agent safe?'], np='the AI Agent and wallets', k='agent wallet safe control')
q('agent', 'Why does the AI Agent page say offline or demo?',
  'The page shows the agent\'s real status. When it is not running, or when no activity has been posted yet, it says so instead of pretending.',
  [], np='the agent status', k='agent offline demo status')
q('agent', 'Can I talk to the AI Agent?',
  'Not yet. The page is a read-only feed. Questions for the team go to @Mrsnakebaby on X.',
  [], vp='talk to the AI Agent', k='chat talk agent')

# ---------------------------------------------------------------- safety and scams
q('safety', 'Will MemeCapes ever ask for my seed phrase?',
  'Never. Nobody from MemeCapes will ever ask for your seed phrase, private key or password, and we never message you first to send money or to "verify" a wallet. Anyone who does is a scammer. Never type a seed phrase into any website.',
  ['Is it safe to give my seed phrase?', 'Someone from MemeCapes asked for my private key'], np='seed phrase requests', k='seed phrase private key never ask scam', top=True)
q('safety', 'How do I know a link or address is official?',
  'Official addresses and links are only posted on memecapes.com and by @Mrsnakebaby on X. Anything else using the MemeCapes name, logo or $CAPES is fake. When in doubt, type memecapes.com yourself.',
  ['Is this the real MemeCapes site?', 'Fake MemeCapes websites'], np='official links', k='official link fake site address')
q('safety', 'I found a fake $CAPES token',
  'Do not buy it. No $CAPES exists until it is announced on memecapes.com and @Mrsnakebaby, and when it does the address is posted there only. Report the fake to the platform where you saw it.',
  ['Someone is selling $CAPES'], np='fake tokens', k='fake token scam capes')
q('safety', 'How does MemeCapes keep me safe?',
  'We never hold your wallet, keys or money; every payment goes straight from your wallet and you see the exact transfer before you approve it. The game server has an always-on guard that blocks attacks, password guessing and floods, and an outside watcher checks that every page you load is exactly the one we published. See the Security page.',
  ['Is MemeCapes secure?', 'What protects my account?'], np='security', k='secure safe guard sentinel watchtower')
q('safety', 'What should I do if I think I was scammed?',
  'Stop sending anything. Blockchain transfers cannot be reversed, so there is usually no way to get crypto back, but tell us: report the player in game with /report or message @Mrsnakebaby on X with screenshots so we can ban them and warn others.',
  ['I got scammed', 'Can you reverse a transaction?'], np='being scammed', k='scammed reverse transaction report')
q('safety', 'Safe habits for playing a game with crypto features',
  'Use a separate password for MemeCapes, keep your seed phrase offline and never type it anywhere, read every transfer in your wallet before approving, trust only memecapes.com and @Mrsnakebaby for links and addresses, and treat anyone who messages you first about money as a scammer.',
  ['Security tips', 'How do I stay safe?'], np='safety tips', k='tips safe habits security')
q('safety', 'Is the game server guarded against attacks?',
  'Yes. An always-on guard inside the servers rate-limits floods, stops password guessing and blocks abusive addresses, and it can pause sign-ups and uploads on its own if something looks wrong. We do not publish the details, for obvious reasons.',
  ['What is Sentinel?', 'What is Watchtower?'], np='the server guard', k='sentinel watchtower guard attack ddos')
q('safety', 'Why was I blocked for a while?',
  'The guard blocks an address for a while when it sees too many wrong passwords, floods of requests or probing. If you were just playing normally, wait a bit and try again; a shared network (school, office, VPN) can be blocked because of someone else on it.',
  ['It says blocked for a while'], np='a temporary block', k='blocked for a while guard')
q('safety', 'Does MemeCapes use trackers or ads?',
  'No analytics trackers and no ad networks. The only ads are the ones projects buy in the shop, shown in the game and on the home page. See the Privacy Policy.',
  ['Do you track me?'], np='tracking', k='tracker analytics privacy ads')
q('safety', 'Can a custom link or QR code be a scam?',
  'Yes. Links sent in chat, DMs or by "support" that ask you to connect a wallet or sign something are the classic scam. MemeCapes never asks you to sign anything outside the game\'s own bank link and the shop\'s own pages on memecapes.com.',
  ['Wallet drainer', 'Someone sent me a link to claim $CAPES'], np='scam links', k='drainer link claim airdrop scam')
q('safety', 'Is there an airdrop?',
  'No. Anything offering a MemeCapes or $CAPES airdrop is a scam. The only free things are earned in the game and the holder perks described on the $CAPES page.',
  ['Free $CAPES airdrop'], np='airdrops', k='airdrop free scam')

# ---------------------------------------------------------------- technical problems
q('tech', 'The game is slow or laggy',
  'Open the game settings and turn Shadows off, close other tabs and apps, and make sure the browser is up to date. Big towns and dense forests are the heaviest spots. On very old devices the game lowers detail by itself.',
  ['How do I make the game run faster?', 'Low FPS', 'The game stutters'], np='lag', k='lag slow fps performance stutter', top=True)
q('tech', 'The screen is black or blank',
  'The browser could not start the 3D world. Reload the page; if it stays blank, update the browser, turn on hardware acceleration in the browser settings, or try another browser. Very old devices without WebGL cannot run the game.',
  ['Black screen', 'Nothing loads', 'White screen'], np='a black screen', k='black blank screen webgl')
q('tech', 'The game froze',
  'Reload the page. Your progress is saved on the server (with an account) or in the browser (offline), so you lose at most a few seconds.',
  ['The game is stuck', 'Frozen screen'], np='a frozen game', k='froze frozen stuck reload')
q('tech', 'Why did my progress disappear?',
  'Guest and offline saves live in the browser on that one device: clearing site data, private browsing, a different browser or a different device will not have them. With an account your save is on the server; make sure you logged in rather than playing as a guest.',
  ['I lost my progress', 'My character is gone', 'Save deleted'], np='lost progress', k='lost progress gone deleted save', top=True)
q('tech', 'Is there sound?',
  'Not yet. Music and sound effects are on the list after the world and the quests.',
  ['Why is there no music?', 'How do I turn on sound?'], np='sound', k='sound music audio')
q('tech', 'How do I turn off shadows or see-through buildings?',
  'In the game settings: Shadows on or off, See-through big buildings on or off, and the body style. Settings are saved with your character.',
  ['Where are the settings?', 'Game options'], np='the settings', k='settings options shadows see-through')
q('tech', 'Why do big buildings go see-through?',
  'When the castle or a massive building stands between the camera and you it fades so you can see yourself. Trees, houses and small things never disappear: turn the camera instead. You can switch the effect off in the settings.',
  ['Buildings disappear when I walk behind them'], np='see-through buildings', k='see-through transparent buildings')
q('tech', 'How much data does the game use?',
  'The first load fetches the world, models and trees (a few megabytes); after that the browser caches them and play uses very little. Updates re-download only what changed.',
  ['Does it use a lot of mobile data?'], np='data use', k='data usage megabytes mobile')
q('tech', 'The text is too small on my phone',
  'Use your phone\'s browser zoom or font settings; the game panel scales with the screen. A bigger text option is on the list.',
  [], np='text size', k='text small font size')
q('tech', 'Can I play in landscape?',
  'Yes on a tablet or computer. On a phone the game is designed for portrait, with the world on top and the panel below.',
  ['Portrait or landscape?'], np='screen orientation', k='landscape portrait orientation')
q('tech', 'The game says a new version is available',
  'Reload the page to get the latest build. Updates are small and your save is kept.',
  ['How do I update the game?'], vp='update the game', k='update new version reload build')
q('tech', 'I see an error message, what do I do?',
  'Reload first. If it keeps happening, note what you were doing, the device and browser, and send that with a screenshot to @Mrsnakebaby on X. Every report helps.',
  ['How do I report a bug?', 'Found a bug'], vp='report a bug', k='bug error report crash')
q('tech', 'Does the game work on a VPN or at school?',
  'Usually. Some strict networks block the game\'s live connection; the start screen then shows Offline and you can play offline. Try another network for online play.',
  ['Blocked at work', 'VPN problems'], np='restricted networks', k='vpn school work network blocked')
q('tech', 'Why does the game look different from the screenshots?',
  'The world changes with every update, and the game lowers detail on slow devices. Screenshots on the site are real in-game shots from a computer.',
  [], np='graphics differences', k='graphics look different screenshots')
q('tech', 'Can I play with a controller?',
  'Not yet. Touch, mouse and keyboard only for now.',
  ['Gamepad support'], np='controller support', k='controller gamepad')
q('tech', 'How do I clear the game cache?',
  'Clear the site data for memecapes.com in your browser settings. Warning: that also deletes an offline or guest save on that device. Account saves are on the server and are not affected.',
  [], vp='clear the cache', k='cache clear site data')

# ---------------------------------------------------------------- rules, terms and privacy
q('rules', 'What are the rules?',
  'Do not cheat, bot, exploit bugs, attack the site or servers, harass other players, impersonate MemeCapes, or post content that is illegal, hateful, sexual, violent or infringing. No scams, no market manipulation, no promoting other tokens without buying an ad. Breaking them gets content removed and accounts suspended or banned.',
  ['What gets you banned?', 'Code of conduct'], np='the rules', k='rules banned conduct cheat', top=True)
q('rules', 'Can I use a bot or macro?',
  'No. Botting, macros and exploiting bugs are against the rules and get accounts banned. The computer-controlled characters in the world are ours and are disclosed; players may not automate play.',
  ['Is autoclicking allowed?'], np='botting', k='bot macro autoclick cheat')
q('rules', 'I was banned. Can I appeal?',
  'Message @Mrsnakebaby on X with your username. Bans for cheating, scamming or harassment are rarely lifted, but every appeal is read.',
  ['Ban appeal', 'Why was I banned?'], vp='appeal a ban', k='ban appeal banned')
q('rules', 'Where are the Terms of Service?',
  'On the site under Terms (the link at the bottom of every page). You agree to them when you pass the age gate, and the site asks again whenever they change.',
  ['What am I agreeing to?'], np='the Terms of Service', k='terms service agreement')
q('rules', 'Where is the Privacy Policy?',
  'Under Privacy at the bottom of the site. Short version: no analytics trackers, no ad networks, nothing sold about you. What you send us (a message, an order) is used only to answer you and deliver the order.',
  ['What data do you collect?'], np='the Privacy Policy', k='privacy policy data collect')
q('rules', 'What data does the game store about me?',
  'With an account: your username, a protected form of your password, your character and its progress, and a linked wallet address if you choose to link one. Nothing else: no email, no phone, no name. Guest play stores everything in your own browser.',
  ['Do you store my personal information?'], np='stored data', k='data stored personal information')
q('rules', 'Are the memes licensed?',
  'MemeCapes is a parody. Its characters are original interpretations inspired by internet culture; some well-known memes may be redesigned after legal review. MemeCapes and $CAPES are not affiliated with or endorsed by the creators of any meme shown.',
  ['Is this official Doge or Pepe?'], np='meme licensing', k='licensed parody affiliated endorsed')
q('rules', 'Is MemeCapes connected to any other game?',
  'No. It is an original game made by one person, inspired by the classic MMOs of the 2000s. It is not affiliated with or endorsed by any other game or company.',
  ['Is this made by a big studio?'], np='affiliation with other games', k='connected other game affiliated')
q('rules', 'Can I stream or make videos of the game?',
  'Yes, please do. You may share screenshots and videos of the game. You may not copy the game, its art or its code to make or sell something else.',
  ['Can I post gameplay on YouTube?', 'Content creator rules'], vp='make videos of the game', k='youtube videos screenshots content creator')
q('rules', 'Can I use MemeCapes art for my own project?',
  'The game, its world, writing, art and the MemeCapes name and medallion belong to MemeCapes. Screenshots and videos for sharing are fine; copying the art or code for something else is not.',
  [], np='using the art', k='art copy use project')
q('rules', 'Where do I send legal notices or takedown requests?',
  'Message @Mrsnakebaby on X, or use the contact details at the bottom of the site. Include what the notice is about and how to reach you.',
  ['DMCA', 'Copyright complaint'], np='legal notices', k='legal notice dmca takedown copyright')
q('rules', 'Is MemeCapes gambling?',
  'No. There is no betting, no loot boxes bought with money and no cash prizes. Random drops in the game are earned by playing, not purchased.',
  ['Are there loot boxes?'], np='gambling', k='gambling loot boxes')

# ---------------------------------------------------------------- about
q('about', 'Who makes MemeCapes?',
  'One builder, @Mrsnakebaby on X, with AI tools, building in public. Follow there for every update.',
  ['Who is the developer?', 'How big is the team?'], np='the team', k='who makes developer team builder', top=True)
q('about', 'How do I contact support?',
  'Search this page first; most answers are here. For anything else, message @Mrsnakebaby on X. In game, /report handles player reports. We never message you first and never ask for passwords or seed phrases.',
  ['How do I reach the team?', 'Contact', 'Is there a support email?'], vp='contact support', np='support', k='contact support help email', top=True)
q('about', 'When is the next update?',
  'The Roadmap page lists what is coming and in what order. Updates ship when they are fun; follow @Mrsnakebaby for the announcement.',
  ['What is coming next?', 'When does the game launch?'], np='the next update', k='next update launch when roadmap')
q('about', 'What is on the roadmap?',
  'Six story updates, three minigames, three new skills and the cape that ties it together: The Great Rug, Maps and Capes, Stonks and Bonds, The Jeet Invasion, The Copium Mines, The Burn and The Final Rug. The Roadmap page has the detail.',
  ['Future plans', 'What features are planned?'], np='the roadmap', k='roadmap plans future features')
q('about', 'Is MemeCapes finished?',
  'No, and it says so: it is in active development and built in public. Things change, get rebalanced and sometimes break; game data can be reset during testing.',
  ['Is the game in beta?'], np='the beta', k='beta finished development reset')
q('about', 'Can I help or contribute?',
  'Play, report bugs, and tell us what is fun and what is not. Feedback goes to @Mrsnakebaby on X. Projects that want to be in the game use the Shop.',
  ['How can I support the project?', 'Are you hiring?'], vp='help the project', k='help contribute feedback hiring')
q('about', 'Where can I follow the news?',
  'On X at @Mrsnakebaby, and on the site: the Roadmap and the home page. Official news comes only from those places.',
  ['Is there a Discord?', 'Is there a Telegram?', 'Social media'], np='the news channels', k='news follow x twitter discord telegram social')
q('about', 'Why meme coins?',
  'Because the internet became a world. Meme coins are the monsters, their real market caps set their levels, and the game pokes fun at all of it. You do not need to own or understand any coin to play.',
  ['Do I need to know about crypto to play?'], np='the meme-coin theme', k='why meme coins theme crypto')
q('about', 'What does "Cape Day" mean?',
  'The name of the launch update: Castle Gigachad, the eight meme towns and the Great Rug chapter, all live for everyone. The home page says when.',
  [], np='Cape Day', k='cape day launch')
q('about', 'Is MemeCapes open source?',
  'The site and game files are served from a public repository so anyone can check that what you load is what was published, but the game is not licensed for reuse: see the Terms.',
  ['Can I see the code?'], np='open source', k='open source code repository')

# ---------------------------------------------------------------- write
# The page turns each verb phrase (vp) and noun phrase (np) into the ways people ask. 'pl' marks plural noun phrases
# so the templates say "what are" instead of "what is".
SINGULAR = {'the server status', 'the Wildlands', 'Diamond Hands', 'HODL Heights', 'Chad Falls', 'Wojak Blues',
            'Touch Grass', 'the tokenomics', 'keeping skins', 'the streamer pass', 'the agent status', 'lost progress',
            'affiliation with other games', 'tips and subscriptions', 'the AI Agent and wallets', 'Feels Bad Man',
            'Much Wow Such Cake', 'The Fish Are Rugged', 'Proof of Work'}
for e in E:
    n = e['np']
    e['pl'] = 1 if n and n.endswith('s') and not n.endswith('ss') and n not in SINGULAR else 0
VP = ['How do I {}?', 'Can I {}?', 'How can I {}?', 'How to {}', 'Where do I {}?', 'Is it possible to {}?',
      'What is the way to {}?', 'I want to {}', 'I can\'t {}', 'Help me {}', 'Steps to {}', 'How would I {}?',
      'Is there a way to {}?', 'Show me how to {}', 'I am trying to {}', 'What do I need to {}?', 'Tell me how to {}',
      'I can\'t figure out how to {}', 'Any way to {}?', '{}?', 'Best way to {}', 'How does one {}?', 'I would like to {}',
      'Why can\'t I {}?', 'What happens when I {}?', 'How am I supposed to {}?', 'Explain how to {}', 'Quick question: how do I {}?',
      'Is it hard to {}?', 'Does the game let me {}?', 'Where can I {}?', 'How do you {}?']
NP = ['What {is} {}?', 'How {does} {} work?', 'Tell me about {}', 'Explain {}', 'I have a question about {}', 'Help with {}',
      '{}?', 'Can you explain {}?', 'What do I need to know about {}?', 'Info on {}', 'What should I know about {}?',
      'Any tips on {}?', 'Details about {}', 'I don\'t understand {}', '{} explained', 'What is the deal with {}?',
      'Guide to {}', '{} help', 'Everything about {}', 'Quick question about {}', 'Where can I read about {}?',
      'Can someone explain {}?', 'I am confused about {}', 'Looking for info on {}', 'Basics of {}', 'What {is} {} exactly?',
      'How {does} {} work in MemeCapes?', 'Tell me more about {}', 'What {is} {} for?', 'Why {does} {} matter?',
      '{} question', 'Is there a guide to {}?', 'What about {}?', 'I need help with {}', 'Can you tell me about {}?',
      'Where do I learn about {}?', 'What {is} {} in the game?', 'Walk me through {}', 'Explain {} to a new player',
      'What {does} {} mean?']
out = {'topics': [{'id': i, 'name': n} for i, n in T.items()], 'vp': VP, 'np': NP, 'qa': E}
os.makedirs('support', exist_ok=True)
json.dump(out, open('support/qa.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(E), 'answers,', sum(1 for e in E if e['top']), 'popular,', os.path.getsize('support/qa.json') // 1024, 'KB')
