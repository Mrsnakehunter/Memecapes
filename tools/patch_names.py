#!/usr/bin/env python3
"""Unique names: skilling pets and the pet messages are our own, not borrowed.
Run from the repo root as part of the build:  python3 tools/patch_names.py
"""
PATH = 'play.html'
h = open(PATH, encoding='utf-8').read()


def rep(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n}: {old[:90]!r}'
    h = h.replace(old, new)


# skilling pets: woodcutting, mining, fishing
rep("const PETN=['','Doge pup','Shiba pup','WIF pup','Bonk Hound pup','Golden Hound pup','Beaver','Rock golem','Heron'];",
    "const PETN=['','Doge pup','Shiba pup','WIF pup','Bonk Hound pup','Golden Hound pup','Lumber Chonk','Pet Rock','Gull of Wall Street'];")
# pet drop messages
rep('say("You have a funny feeling like you\'re being followed.",\'#e6398f\')',
    'say("Something small scurries after you. Looks like you have a pet!",\'#e6398f\')', count=3)
rep('say("You have a funny feeling like you would have been followed...",\'#e6398f\')',
    'say("Something small tries to follow you, but your pet shoos it off.",\'#e6398f\')')

open(PATH, 'w', encoding='utf-8').write(h)
print('names patch applied')
