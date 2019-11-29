import json
import pathlib

import attr
import lingpy

from clldutils.misc import slug
from pylexibank import Concept, Language, Dataset as BaseDataset, progressbar


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
    dir = pathlib.Path(__file__).parent
    concept_class = OurConcept
    language_class = OurLanguage
    id = 'sagartst'

    def cmd_download(self, args):
        data = json.loads(self.raw_dir.joinpath('data.json').read_text(encoding='utf8'))
        self.raw_dir.download(data['url'], 'sino-tibetan-raw.tsv')

    def cmd_makecldf(self, args):
        data = json.loads(self.raw_dir.joinpath('data.json').read_text(encoding='utf8'))
        wl = lingpy.Wordlist(str(self.raw_dir / 'sino-tibetan-raw.tsv'))
        profile = {l[0]: l[1] for l in lingpy.csv2list(str(self.raw_dir / 'profile.tsv'))}

        for idx, tokens in progressbar(wl.iter_rows('tokens'), desc='tokenize'):
            tks = []
            for token in tokens:
                tks.extend(
                    profile.get(
                        token,
                        profile.get(token.split('/')[1] if '/' in token else token, token)
                    ).split(' '))
            wl[idx, 'tokens'] = [x.strip() for x in tks if x != 'NULL' and x.strip()]

        args.writer.add_sources()
        args.writer.add_languages()
        concept2id = {}
        for c in self.conceptlists[0].concepts.values():
            args.writer.add_concept(
                ID=c.concepticon_id,
                TBL_ID=c.attributes['huang_1992_1820'],
                Name=c.english,
                Coverage=c.attributes['coverage'],
                Concepticon_ID=c.concepticon_id
            )
            concept2id[c.english] = c.concepticon_id

        source_dict, langs_dict = {}, {}
        for l in self.languages:
            source_dict[l['Name']] = l['Source']
            langs_dict[l['Name']] = l['ID']

        wl.output(
            'tsv',
            filename=str(self.raw_dir / 'sino-tibetan-cleaned'),
            subset=True,
            rows={"ID": "not in "+str(data['blacklist'])}
        )

        for k in progressbar(wl, desc='wl-to-cldf'):
            if wl[k, 'tokens']:
                row = args.writer.add_form_with_segments(
                    Language_ID=langs_dict.get(
                        data['taxa'].get(wl[k, 'doculect'], wl[k, 'doculect'])),
                    Parameter_ID=concept2id[wl[k, 'concept']],
                    Value=wl[k, 'entry_in_source'].strip()
                        or ''.join(wl[k, 'tokens']) or wl[k, 'ipa'],
                    Form=wl[k, 'ipa'] or wl[k, 'entry_in_source'] or ''.join(wl[k, 'tokens']),
                    Segments=wl[k, 'tokens'],
                    Source=source_dict.get(data['taxa'].get(
                        wl[k, 'doculect'], wl[k, 'doculect'])).split(','),
                    Comment=wl[k, 'note'],
                    Cognacy=wl[k, 'cogid'],
                    Loan=True if wl[k,'borrowing'].strip() else False
                )

                cid = slug(wl[k, 'concept'])+'-'+'{0}'.format(wl[k, 'cogid'])
                args.writer.add_cognate(
                    lexeme=row,
                    Cognateset_ID=cid,
                    Source='Sagart2018',
                    Alignment='',
                    Alignment_Source=''
                )
