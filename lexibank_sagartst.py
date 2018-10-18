# coding=utf-8
from __future__ import unicode_literals, print_function

import attr
import lingpy
from pycldf.sources import Source

from clldutils.path import Path
from clldutils.misc import slug
from pylexibank.dataset import Metadata, Concept, Language
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.util import pb, get_url, textdump
import json
from urllib import request


@attr.s
class OurConcept(Concept):
    TBL_ID = attr.ib(default=None)
    Coverage = attr.ib(default=None)

@attr.s
class OurLanguage(Language):
    Name_in_Text = attr.ib(default=None)
    Name_in_Source = attr.ib(default=None)
    Subgroup = attr.ib(default=None)
    Coverage = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    Latitude = attr.ib(default=None)
    Source = attr.ib(default=None)

    

class Dataset(BaseDataset):
    dir = Path(__file__).parent
    concept_class = OurConcept
    language_class = OurLanguage
    id = 'sagartst'


    def cmd_download(self, **kw):
        data = json.load(open(self.raw.posix('data.json')))
        self.raw.download(
                data['url'],
                'sino-tibetan-raw.tsv'
                )

    def split_forms(self, item, value):
        value = self.lexemes.get(value, value)
        return [self.clean_form(item, form) for form in [value]]

    def cmd_install(self, **kw):
        data = json.load(open(self.raw.posix('data.json')))
        wl = lingpy.Wordlist(self.raw.posix('sino-tibetan-raw.tsv'))
        profile = {l[0]: l[1] for l in lingpy.csv2list(
            self.raw.posix('profile.tsv'))}
        for idx, tokens in pb(wl.iter_rows(
            'tokens'), desc='tokenize'):
            tks = []
            for token in tokens:
                tks += profile.get(
                    token, 
                    profile.get(
                        token.split('/')[1] if '/' in token else token,
                        token
                        )
                    ).split(' ')
            wl[idx, 'tokens'] = [x.strip() for x in tks if x != 'NULL' and
                    x.strip()]

        with self.cldf as ds:
            ds.add_sources(*self.raw.read_bib())
            ds.add_languages(id_factory=lambda l: l['Name'])
            for c in self.concepts:
                ds.add_concept(
                        ID=c['CONCEPTICON_ID'],
                        TBL_ID=c['TBL_ID'],
                        Name=c['ENGLISH'],
                        Coverage=c['Coverage']
                        )
            concept2id = {c['ENGLISH']: c['CONCEPTICON_ID'] for c in self.concepts}
            source_dict = {}
            concept_dict = {}
            for l in self.languages:
                source_dict[l['Name']] = l['Source']

            wl.output(
                    'tsv', 
                    filename=self.raw.posix('sino-tibetan-cleaned'), 
                    subset=True,
                    rows={"ID": "not in "+str(data['blacklist'])}
                    )

            for k in pb(wl, desc='wl-to-cldf'):
                if wl[k, 'tokens']:
                    for row in ds.add_lexemes(
                        Language_ID=data['taxa'].get(
                            wl[k, 'doculect'], 
                            wl[k, 'doculect']),
                        Parameter_ID=concept2id[wl[k, 'concept']],
                        Value=wl[k, 'entry_in_source'].strip() or ''.join(wl[k,
                            'tokens']),
                        Form=wl[k, 'ipa'],
                        Segments=wl[k, 'tokens'],
                        Source=source_dict.get(data['taxa'].get(
                                wl[k, 'doculect'], 
                                wl[k, 'doculect'])).split(','),
                        Comment=wl[k, 'note'],
                        Cognacy=wl[k, 'cogid'],
                        Loan=True if wl[k,'borrowing'].strip() else False
                        ):

                        cid = slug(wl[k, 'concept'])+'-'+'{0}'.format(wl[k,
                            'cogid'])
                        ds.add_cognate(
                                lexeme=row,
                                Cognateset_ID=cid,
                                Source='Sagart2018',
                                Alignment='',
                                Alignment_Source=''
                                )


