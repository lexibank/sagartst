from lingpy import *
from collections import defaultdict
from sys import argv
from tabulate import tabulate

refine = {
        "Bodic": "Tani-Yidu",
        "Burmish": "Lolo-Burmese",
        "Chepang": "Chepang",
        "Chin": "Kuki-Chin",
        "Deng": "Tani-Yidu",
        "Garo": "Sal",
        "Jingpho": "Sal",
        "Kiranti": "Kiranti",
        "Koch": "Sal",
        "Loloish": "Lolo-Burmese",
        "Mikir": "Kuki-Chin",
        "Mizo": "Kuki-Chin",
        "Naga": "Kuki-Chin",
        "Nungic": "Dulong",
        "Qiangic": "rGyalrong",
        "Sinitic": "Sinitic",
        "Tangut": "rGyalrong",
        "Tani": "Tani-Yidu",
        "Tibetan": "Tibetan",
        "Tibeto-Kinauri": "Tibeto-Kinauri",
        "rGyalrong": "rGyalrong"
        }


valid_groups = [
        "Sinitic",
        "rGyalrong",
        "Tibeto-Kinauri",
        "Kuki-Chin",
        "Lolo-Burmese",
        "Sal",
        "Tani-Yidu",
        "Kiranti",
        "Tibetan"]

wl = Wordlist(argv[1])
etd = wl.get_etymdict(ref=argv[2])
xfam = {}
for cogid, vals in etd.items():
    idxs = []
    for v in vals:
        if v:
            idxs += v
    fams = [refine.get(wl[idx, "subgroup"], wl[idx, "subgroup"]) for idx in idxs]
    concept = wl[idxs[0], "concept"]
    if len(set(fams)) > 1:
        if concept in xfam:
            xfam[concept] += [(cogid, "/".join(sorted(set(fams))))]
        else:
            xfam[concept] = [(cogid, "/".join(sorted(set(fams))))]
table = []

for cogid, vals in xfam.items():
    for val in vals:
        table += [[cogid, val[0], val[1]]]

if "full" in argv:
    print(tabulate(sorted(table, key=lambda x: (x[-1], x[0], x[1])), headers=["concept", "cognate set", "language families"], tablefmt="pipe"))
else:

    counts = defaultdict(int)
    for row in table:
        counts[row[-1]] += 1
    table = []
    
    for row in sorted(counts.items(), key=lambda x: len(x[0].split('/')),
            reverse=True):
        table += [[row[0], len(row[0].split('/')), row[1]]]
    print(tabulate(table, headers=["Subgroups", "Size", "Cognates"], tablefmt="pipe"))

    
