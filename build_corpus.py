#!/usr/bin/env python3
"""Build the neuroscience/cognitive-science library from the raw arXiv snapshot, in one pass.
Usage: python build_corpus.py arxiv-metadata-oai-snapshot-001.json data/corpus.jsonl.gz
Keeps papers tagged q-bio.NC, cs.AI or cs.NE; scopes to the q-bio.NC spine plus cs.AI/cs.NE
papers cross-listed to q-bio* or matching neuroscience/cognition keywords. Writes the gz corpus
and data/corpus_meta.json with the true counts."""
import json, gzip, re, sys
from collections import Counter
INP = sys.argv[1] if len(sys.argv) > 1 else "arxiv-metadata-oai-snapshot-001.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/corpus.jsonl.gz"
TARGET = {"q-bio.NC", "cs.AI", "cs.NE"}
NEURO = re.compile(r"brain|neuron|neuronal|synap|cortex|cortical|cerebr|hippocamp|dendrit|axon|"
                   r"amygdala|thalam|striat|\beeg\b|\bmeg\b|fmri|electrophysiolog|neuroimag|"
                   r"neurosci|cognit|psychophys|connectom|spiking|neuromorphic", re.I)
full, scoped, seen = Counter(), Counter(), set()
nkept = 0
with open(INP, encoding="utf-8", errors="ignore") as f, gzip.open(OUT, "wt", encoding="utf-8") as w:
    for line in f:
        if "q-bio.NC" not in line and "cs.AI" not in line and "cs.NE" not in line:
            continue
        try: r = json.loads(line)
        except Exception: continue
        cats = set(r.get("categories", "").split())
        if not cats & TARGET: continue
        pid = r.get("id", "")
        if not pid or pid in seen: continue
        seen.add(pid)
        for c in cats & TARGET: full[c] += 1
        text = (r.get("title") or "") + " " + (r.get("abstract") or "")
        keep = ("q-bio.NC" in cats) or ((cats & {"cs.AI", "cs.NE"}) and
               (any(c.startswith("q-bio") for c in cats) or NEURO.search(text)))
        if keep:
            nkept += 1
            for c in cats & TARGET: scoped[c] += 1
            w.write(json.dumps({"id": pid,
                "title": (r.get("title") or "").replace("\n", " ").strip(),
                "abstract": (r.get("abstract") or "").replace("\n", " ").strip(),
                "categories": r.get("categories", "")}, ensure_ascii=False) + "\n")
json.dump({"full_superset_unique_papers": len(seen), "full_per_category": dict(full),
           "scoped_papers": nkept, "scoped_per_category": dict(scoped)},
          open("data/corpus_meta.json", "w"), indent=2)
print(f"superset {len(seen)} papers, per-category {dict(full)}; scoped hits {dict(scoped)} -> {OUT}")
