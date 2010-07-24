#!/usr/bin/python
# -*- coding: utf-8 -*-
from urllib import urlopen
from textwrap import wrap
import re

BASE_URL = 'http://www.emag.ro/resigilate/p%s?&catid=91&pret=-1'
EMAG_URL = 'http://www.emag.ro'
MAX_PAGES = 6
LINE_WRAP = 70

# '<a href="/notebook_laptop/LINK?ref=ocz#ocazii" class="produs_lista" '
# 'style="color:#049A07; font-size:14px;">NUME</a><br />
produs_regex = re.compile(
    '<a href="(/notebook_laptop/.*)\?ref=ocz#ocazii" class="produs_lista" '
    'style="color:#049A07; font-size:14px;">(.*)</a><br />')

# '<strong>Tip procesor:</strong> '
# 'Intel® Core<SMALL><SUP>TM</SUP></SMALL>2 Extreme<br />'
procesor_regex = re.compile(
    '<strong>Tip procesor:</strong> (.*)<br />')

# <strong>Frecventa procesor:</strong> 1730 MHz<br />
frecventa_regex = re.compile(
    '<strong>Frecventa procesor:</strong> (.*) MHz<br />')

# '<strong>Diagonala:</strong> 17 inch<br />'
diagonala_regex = re.compile(
    '<strong>Diagonala:</strong> (.*) inch<br />')

# <span style="color:#049A07;font-size:12px;">14.499,99 RON</span>
pret_regex = re.compile(
    '<span style="color:#049A07;font-size:12px;">(.*) RON</span>')

# '<div style="color:#000000; position:relative; padding-left:5px; '
# 'float:left">Text descriere'
stare_regex = re.compile(
    '<div style="color:#000000; position:relative; '
    'padding-left:5px; float:left">(.*)')

def nice_wrap(text):
    separator = "\n           "
    text = text.replace('<SMALL><SUP>TM</SUP></SMALL>', ' ')
    return separator.join(wrap(text, LINE_WRAP-len(separator)))


def arata_produs(produs):
    print nice_wrap('Nume:      %s' % (produs['nume']))
    print nice_wrap('Procesor:  %s' % (produs['procesor']))
    print nice_wrap('Frecventa: %s MHz' % (produs['frecventa']))
    print nice_wrap('Diagonala: %s inch' % (produs['diagonala']))
    print nice_wrap('Stare:     %s' % (produs['stare']))
    print nice_wrap('Garantie:  %d luni' % (produs['garantie']))
    print nice_wrap('Pret:      %d' % (produs['pret']))
    print ''
    print 'Link:      %s' % (EMAG_URL + produs['link'])
    print '-' * LINE_WRAP
    print ''

def filtreaza_produs(produs):
    filtrat = True
    if (re.search('(i5)|(i3)|(i7)', produs['procesor']) and
        produs['pret'] < 4001 and
        produs['diagonala'] < 15):
        filtrat = False
    if filtrat is False:
        arata_produs(produs)

produs = {}
for index in xrange(1, MAX_PAGES+1):
    page = urlopen(BASE_URL % (index))
    for line in page:

        produs_search = produs_regex.search(line)
        if produs_search:
            produs['link'] = produs_search.group(1)
            produs['nume'] = produs_search.group(2)

        procesor_search = procesor_regex.search(line)
        if procesor_search:
            produs['procesor'] = procesor_search.group(1)

        frecventa_search = frecventa_regex.search(line)
        if frecventa_search:
            produs['frecventa'] = int(frecventa_search.group(1))

        diagonala_search = diagonala_regex.search(line)
        if diagonala_search:
            produs['diagonala'] = float(diagonala_search.group(1))

        stare_search = stare_regex.search(line)
        if stare_search:
            if produs.has_key('stare') is False:
                produs['stare'] = stare_search.group(1)
            else:
                produs['garantie'] = int(
                    stare_search.group(1).replace(' luni</div>', ''))

        pret_search = pret_regex.search(line)
        if pret_search:
            produs['pret'] = float(
                pret_search.group(1).replace('.', '').replace(',', '.'))
            filtreaza_produs(produs)
            produs = {}
