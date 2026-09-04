"""Eksploracja i kontrola jakości danych + redukcja wymiarów (do Raportów 3 i 4)."""
import json, gzip, re, hashlib
from collections import Counter
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA, OUT = "data", "out"
import os; os.makedirs(OUT, exist_ok=True)

ids, titles, abstracts, cats = [], [], [], []
with gzip.open(f"{DATA}/corpus.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        ids.append(r["id"]); titles.append((r.get("title") or "").strip())
        abstracts.append((r.get("abstract") or "").strip()); cats.append(r.get("categories", "").split())
N = len(ids)
rep = {}
rep["n_papers"] = N
rep["n_unique_ids"] = len(set(ids))
rep["missing_title"] = sum(1 for t in titles if not t)
rep["missing_abstract"] = sum(1 for a in abstracts if not a)
rep["missing_categories"] = sum(1 for c in cats if not c)

# duplikaty treści
h = [hashlib.md5((t + a).lower().encode()).hexdigest() for t, a in zip(titles, abstracts)]
rep["duplicate_text_rows"] = N - len(set(h))
ht = [hashlib.md5(t.lower().encode()).hexdigest() for t in titles]
rep["duplicate_titles"] = N - len(set(ht))

# długości
wl = np.array([len(a.split()) for a in abstracts])
cl = np.array([len(a) for a in abstracts])
tl = np.array([len(t.split()) for t in titles])
rep["abstract_words"] = dict(min=int(wl.min()), q25=int(np.percentile(wl, 25)), median=int(np.median(wl)),
                             mean=round(float(wl.mean()), 1), q75=int(np.percentile(wl, 75)),
                             p90=int(np.percentile(wl, 90)), max=int(wl.max()))
rep["title_words_median"] = int(np.median(tl))
rep["abstracts_under_20_words"] = int((wl < 20).sum())
rep["abstracts_over_400_words"] = int((wl > 400).sum())

# kategorie
flat = Counter(c for cs in cats for c in set(cs))
rep["distinct_categories"] = len(flat)
rep["top20_categories"] = flat.most_common(20)
ncat = np.array([len(set(c)) for c in cats])
rep["categories_per_paper"] = dict(median=int(np.median(ncat)), mean=round(float(ncat.mean()), 2), max=int(ncat.max()))
for k in ("q-bio.NC", "cs.AI", "cs.NE"):
    rep[f"count_{k}"] = flat[k]

# czytelnicy
meta = json.load(open(f"{DATA}/users.json"))
users = meta["users"]
pos = {p: i for i, p in enumerate(ids)}
catsets = [set(c) for c in cats]
rel_sizes = []
for u in users:
    rule = [p.strip() for p in u["topic_rule"].split(" AND ")]
    rel = sum(1 for s in catsets if all(p in s for p in rule))
    rel_sizes.append(rel)
rel_sizes = np.array(rel_sizes)
rep["readers"] = dict(n=len(users), profile_size=meta["profile_size"], gt_cap=meta["gt_cap"],
                      relevant_min=int(rel_sizes.min()), relevant_median=int(np.median(rel_sizes)),
                      relevant_max=int(rel_sizes.max()),
                      readers_with_capped_key=int((rel_sizes - meta["profile_size"] > meta["gt_cap"]).sum()))
rep["class_imbalance"] = round(float(rel_sizes.max() / rel_sizes.min()), 1)

# --- reprezentacja i redukcja wymiarów ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
texts = [f"{t}. {a}".strip() for t, a in zip(titles, abstracts)]
vec = TfidfVectorizer(stop_words="english", min_df=3, max_df=0.5, ngram_range=(1, 2),
                      max_features=50000, sublinear_tf=True)
X = vec.fit_transform(texts)
rep["tfidf"] = dict(features=X.shape[1], nnz=int(X.nnz),
                    sparsity_pct=round(100 * (1 - X.nnz / (X.shape[0] * X.shape[1])), 4),
                    mean_terms_per_doc=round(X.nnz / X.shape[0], 1))
vocab_all = TfidfVectorizer(stop_words="english", min_df=1).fit(texts)
rep["vocab_before_mindf"] = len(vocab_all.vocabulary_)

svd = TruncatedSVD(n_components=150, random_state=42)
Z = svd.fit_transform(X)
ev = np.cumsum(svd.explained_variance_ratio_)
rep["svd"] = {"components": 150, "var_10": round(float(ev[9]), 4), "var_50": round(float(ev[49]), 4),
              "var_100": round(float(ev[99]), 4), "var_150": round(float(ev[-1]), 4)}

# najważniejsze cechy globalnie i w pierwszych składowych
terms = np.array(vec.get_feature_names_out())
mass = np.asarray(X.sum(axis=0)).ravel()
rep["top_terms_by_tfidf_mass"] = [terms[i] for i in np.argsort(-mass)[:25]]
rep["svd_components"] = {f"C{j+1}": [terms[i] for i in np.argsort(-svd.components_[j])[:10]] for j in range(5)}

json.dump(rep, open(f"{OUT}/eda_report.json", "w"), ensure_ascii=False, indent=2)

# --- wykresy ---
fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
ax.hist(wl, bins=60, color="#33691e")
ax.axvline(np.median(wl), color="black", ls="--", lw=1)
ax.text(np.median(wl) + 8, ax.get_ylim()[1] * .9, f"mediana {int(np.median(wl))} słów", fontsize=9)
ax.set_xlabel("długość abstraktu [słowa]"); ax.set_ylabel("liczba artykułów")
ax.set_title("Rozkład długości abstraktów (36 314 artykułów)")
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(f"{OUT}/fig_dlugosc_abstraktow.png"); plt.close(fig)

top = flat.most_common(15)[::-1]
fig, ax = plt.subplots(figsize=(7, 5), dpi=120)
ax.barh([t[0] for t in top], [t[1] for t in top], color="#546e7a")
ax.set_xlabel("liczba artykułów"); ax.set_title("15 najczęstszych kategorii arXiv w korpusie")
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(f"{OUT}/fig_kategorie.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
ax.plot(range(1, 151), ev, color="#283593", lw=2)
for c, lbl in [(10, "10"), (50, "50"), (100, "100")]:
    ax.scatter([c], [ev[c - 1]], color="#283593", zorder=3)
    ax.annotate(f"{lbl} skł. → {ev[c-1]*100:.1f}%", (c, ev[c - 1]), textcoords="offset points",
                xytext=(8, -10), fontsize=9)
ax.set_xlabel("liczba składowych SVD"); ax.set_ylabel("skumulowana wyjaśniona wariancja")
ax.set_title("Redukcja wymiarów macierzy TF-IDF (50 000 → k)")
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(f"{OUT}/fig_svd.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
ax.hist(rel_sizes, bins=40, color="#8bc34a")
ax.axvline(60, color="crimson", ls="--", lw=1.5)
ax.text(70, ax.get_ylim()[1] * .8, "gt_cap = 60\n(obcięcie w oryginale)", fontsize=9, color="crimson")
ax.set_xlabel("liczba artykułów relewantnych dla czytelnika"); ax.set_ylabel("liczba czytelników")
ax.set_title("Wielkość zbioru relewantnego — skala nierównowagi")
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout()
fig.savefig(f"{OUT}/fig_zbior_relewantny.png"); plt.close(fig)

print(json.dumps(rep, ensure_ascii=False, indent=2))
