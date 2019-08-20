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
    SubGroup = attr.ib(default=None)
    Coverage = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    Latitude = attr.ib(default=None)
    Source = attr.ib(default=None)
    Number = attr.ib(default=None)

    

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
            ds.add_languages()
            for c in self.conceptlist.concepts.values():
                ds.add_concept(
                        ID=c.concepticon_id,
                        TBL_ID=c.attributes['huang_1992_1820'],
                        Name=c.english,
                        Coverage=c.attributes['coverage'],
                        Concepticon_ID=c.concepticon_id
                        )
            concept2id = {c.english: c.concepticon_id for c in
                    self.conceptlist.concepts.values()}
            source_dict, langs_dict = {}, {}
            concept_dict = {}
            for l in self.languages:
                source_dict[l['Name']] = l['Source']
                langs_dict[l['Name']] = l['ID']

            wl.output(
                    'tsv', 
                    filename=self.raw.posix('sino-tibetan-cleaned'), 
                    subset=True,
                    rows={"ID": "not in "+str(data['blacklist'])}
                    )

            for k in pb(wl, desc='wl-to-cldf'):
                if wl[k, 'tokens']:
                    row = ds.add_form_with_segments(
                        Language_ID=langs_dict.get(data['taxa'].get(
                            wl[k, 'doculect'],
                            wl[k, 'doculect'])), 
                        Parameter_ID=concept2id[wl[k, 'concept']],
                        Value=wl[k, 'entry_in_source'].strip() or ''.join(wl[k,
                            'tokens']) or wl[k, 'ipa'],
                        Form=wl[k, 'ipa'] or wl[k, 'entry_in_source'] or ''.join(wl[k, 'tokens']),
                        Segments=wl[k, 'tokens'],
                        Source=source_dict.get(data['taxa'].get(
                                wl[k, 'doculect'], 
                                wl[k, 'doculect'])).split(','),
                        Comment=wl[k, 'note'],
                        Cognacy=wl[k, 'cogid'],
                        Loan=True if wl[k,'borrowing'].strip() else False
                        )

                    cid = slug(wl[k, 'concept'])+'-'+'{0}'.format(wl[k,
                        'cogid'])
                    ds.add_cognate(
                            lexeme=row,
                            Cognateset_ID=cid,
                            Source='Sagart2018',
                            Alignment='',
                            Alignment_Source=''
                            )


