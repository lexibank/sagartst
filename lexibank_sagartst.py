import json
import pathlib

import attr
import lingpy
from clldutils.misc import slug
import pylexibank


@attr.s
class CustomConcept(pylexibank.Concept):
    TBL_ID = attr.ib(default=None)
    Coverage = attr.ib(default=None)


@attr.s
class CustomLanguage(pylexibank.Language):
    Name_in_Text = attr.ib(default=None)
    Name_in_Source = attr.ib(default=None)
    SubGroup = attr.ib(default=None)
    Coverage = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    Latitude = attr.ib(default=None)
    Source = attr.ib(default=None)
    Number = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    dir = pathlib.Path(__file__).parent
    concept_class = CustomConcept
    language_class = CustomLanguage
    id = "sagartst"

    def cmd_download(self, args):
        data = json.loads(self.raw_dir.joinpath("data.json").read_text(encoding="utf8"))
        self.raw_dir.download(data["url"], "sino-tibetan-raw.tsv")

    def cmd_makecldf(self, args):
        wl = lingpy.Wordlist(str(self.raw_dir / "sino-tibetan-raw.tsv"))
        args.writer.add_sources()
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            args.writer.add_concept(
                ID=idx,
                TBL_ID=concept.attributes["huang_1992_1820"],
                Name=concept.english,
                Coverage=concept.attributes["coverage"],
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.english] = idx
        languages, sources = {}, {}
        for language in self.languages:
            args.writer.add_language(**language)
            languages[language["Name_in_Source"]] = language["ID"]
            sources[language["Name_in_Source"]] = language["Source"]
        for idx in pylexibank.progressbar(wl, desc="cldfify"):
            if wl[idx, "tokens"] and " ".join(wl[idx, "tokens"]).strip("+"):
                row = args.writer.add_form(
                    Language_ID=languages[wl[idx, "doculect"]],
                    Local_ID=idx,
                    Parameter_ID=concepts[wl[idx, "concept"]],
                    Value=wl[idx, "entry_in_source"].strip()
                    or "".join(wl[idx, "tokens"])
                    or wl[idx, "ipa"],
                    Form=".".join(wl[idx, "tokens"]),
                    Source=sources[wl[idx, "doculect"]].split(","),
                    Comment=wl[idx, "note"],
                    Cognacy=wl[idx, "cogid"],
                    Loan=True if wl[idx, "borrowing"].strip() else False,
                )

                args.writer.add_cognate(
                    lexeme=row,
                    Cognateset_ID=wl[idx, "cogid"],
                    Source="Sagart2018",
                    Alignment="",
                    Alignment_Source="",
                )
