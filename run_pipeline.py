#!/usr/bin/env python3
"""
Pełny pipeline porównania silników rekomendacji artykułów naukowych — wersja skryptowa.

Robi dokładnie to samo co recommender_pipeline.ipynb, ale bez notebooka i bez interfejsu,
żeby dało się uruchomić przy obronie bez internetu i bez Colaba.

Użycie:
    python3 run_pipeline.py                 # wszystko, z modelami semantycznymi
    python3 run_pipeline.py --skip-semantic # tylko leksykalne (sekundy zamiast godzin na CPU)

Wyniki lądują w data/results_*.csv i data/fig_*.png.
Embeddingi są buforowane w data/emb_*.npy — drugie uruchomienie nie liczy ich ponownie.
"""
import os, sys, json, gzip, time, math, random, argparse
from collections import Counter
import numpy as np, pandas as pd
import scipy.sparse as sp

SEED = 42
random.seed(SEED); np.random.seed(SEED)
KS = [5, 10]
DATA = "data"

ap = argparse.ArgumentParser()
ap.add_argument("--skip-semantic", action="store_true", help="pomiń MiniLM i SPECTER2")
ap.add_argument("--data", default=DATA)
args = ap.parse_args()
DATA = args.data
import shutil
os.makedirs(DATA, exist_ok=True)
for fn in ("corpus.jsonl.gz", "users.json"):
    dst = os.path.join(DATA, fn)
    if not os.path.exists(dst) and os.path.exists(fn):
        try: os.link(fn, dst)
        except Exception: shutil.copy(fn, dst)

# ────────────────────────────────────────────────────────────── 1. dane
def load_corpus(path):
    ids, titles, abstracts, cats = [], [], [], []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            ids.append(r["id"])
            titles.append((r.get("title") or "").strip())
            abstracts.append((r.get("abstract") or "").strip())
            cats.append(set(r.get("categories", "").split()))
    return ids, titles, abstracts, cats

ids, titles, abstracts, cats = load_corpus(f"{DATA}/corpus.jsonl.gz")
texts = [f"{t}. {a}".strip() for t, a in zip(titles, abstracts)]
pos = {p: i for i, p in enumerate(ids)}
N = len(ids)
meta = json.load(open(f"{DATA}/users.json"))
users = meta["users"]
print(f"korpus: {N} artykułów, {len(users)} czytelników")

# ──────────────────────────────────────── 2. pełny klucz odpowiedzi (bez gt_cap)
truncated = 0
for u in users:
    rule = [p.strip() for p in u["topic_rule"].split(" AND ")]
    rel = {i for i in range(N) if all(p in cats[i] for p in rule)}
    assert len(rel) == u["n_relevant_total"], f"rekonstrukcja klucza nie zgadza się dla {u['user_id']}"
    u["_profile"] = {pos[p] for p in u["profile_ids"] if p in pos}
    u["_gt"] = rel - u["_profile"]
    assert not (u["_profile"] & u["_gt"]), "artykuł startowy nie może być w kluczu"
    if len(u["_gt"]) > u["n_ground_truth"]:
        truncated += 1
new = np.array([len(u["_gt"]) for u in users])
print(f"klucz odtworzony dla wszystkich {len(users)} czytelników "
      f"(w oryginale obcięty u {truncated}, mediana |GT| {int(np.median(new))}, max {new.max()})")

def _rank(scores, k, exclude):
    s = np.asarray(scores, dtype=np.float64).ravel().copy()
    s[list(exclude)] = -np.inf
    top = np.argpartition(-s, k)[:k]
    return top[np.argsort(-s[top])]

ENGINES, build, qtime = {}, {}, {}

# ────────────────────────────────────────────────────────────── 3. TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
t = time.time()
vec = TfidfVectorizer(stop_words="english", min_df=3, max_df=0.5,
                      ngram_range=(1, 2), max_features=50000, sublinear_tf=True)
X = vec.fit_transform(texts)
build["TF-IDF"] = time.time() - t
print(f"TF-IDF: {X.shape[1]} cech, {build['TF-IDF']:.1f}s")

def recommend_tfidf(profile, k, exclude):
    prof = np.asarray(X[sorted(profile)].mean(axis=0)).ravel()
    return _rank(X.dot(prof), k, exclude)

# ────────────────────────────────────────────────────────────── 4. BM25
t = time.time()
cv = CountVectorizer(stop_words="english", min_df=3, max_df=0.5, max_features=50000)
Cm = cv.fit_transform(texts).astype(np.float32)
dl = np.asarray(Cm.sum(axis=1)).ravel(); avgdl = dl.mean()
df_ = np.asarray((Cm > 0).sum(axis=0)).ravel()
idf = np.log(1 + (N - df_ + 0.5) / (df_ + 0.5)).astype(np.float32)
k1, b = 1.5, 0.75
coo = Cm.tocoo()
w = idf[coo.col] * coo.data * (k1 + 1) / (coo.data + k1 * (1 - b + b * dl[coo.row] / avgdl))
Bm = sp.csr_matrix((w.astype(np.float32), (coo.row, coo.col)), shape=Cm.shape)
build["BM25"] = time.time() - t
print(f"BM25: {Bm.shape[1]} terminów, {build['BM25']:.1f}s")

def recommend_bm25(profile, k, exclude):
    q = (np.asarray(Cm[sorted(profile)].sum(axis=0)).ravel() > 0).astype(np.float32)
    return _rank(Bm.dot(q), k, exclude)

# ────────────────────────────────────────────────────────────── 5. baseline'y
catf = Counter(c for s in cats for c in s)
popscore = np.array([sum(catf[c] for c in cats[i]) for i in range(N)], dtype=float)
pop_order = np.argsort(-popscore)
_rng = random.Random(SEED)
recommend_popularity = lambda profile, k, exclude: [d for d in pop_order if d not in exclude][:k]
recommend_random = lambda profile, k, exclude: _rng.sample([d for d in range(N) if d not in exclude], k)

ENGINES.update({"Random": recommend_random, "Popularity": recommend_popularity,
                "BM25": recommend_bm25, "TF-IDF": recommend_tfidf})

# ────────────────────────────────────────────────────── 6. silniki semantyczne
def encode_corpus(tag):
    """Zwraca macierz zanurzeń (N x d), znormalizowaną L2. Buforuje na dysku."""
    cache = f"{DATA}/emb_{tag}.npy"
    if os.path.exists(cache):
        E = np.load(cache)
        if E.shape[0] == N:
            print(f"wczytano cache {cache} {E.shape}")
            build[{"minilm": "MiniLM", "specter2": "SPECTER2"}[tag]] = 0.0
            return E
    import torch
    torch.set_num_threads(os.cpu_count() or 1)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if tag == "minilm":
        from transformers import AutoTokenizer, AutoModel
        tok = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        mdl = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").to(dev).eval()
        maxlen, bs = 256, 64
        @torch.no_grad()
        def enc(batch):
            bb = tok(batch, padding=True, truncation=True, max_length=maxlen, return_tensors="pt").to(dev)
            out = mdl(**bb).last_hidden_state
            m = bb["attention_mask"].unsqueeze(-1).float()
            v = (out * m).sum(1) / m.sum(1).clamp(min=1e-9)          # mean pooling
            return torch.nn.functional.normalize(v, dim=1).cpu().numpy().astype("float32")
    else:
        from transformers import AutoTokenizer
        from adapters import AutoAdapterModel
        tok = AutoTokenizer.from_pretrained("allenai/specter2_base")
        mdl = AutoAdapterModel.from_pretrained("allenai/specter2_base")
        mdl.load_adapter("allenai/specter2", source="hf", load_as="proximity", set_active=True)
        mdl.set_active_adapters("proximity")
        mdl = mdl.to(dev).eval()
        assert "proximity" in str(mdl.active_adapters), "adapter proximity nieaktywny"
        maxlen, bs = 512, 16
        @torch.no_grad()
        def enc(batch):
            bb = tok(batch, padding=True, truncation=True, max_length=maxlen, return_tensors="pt").to(dev)
            v = mdl(**bb).last_hidden_state[:, 0, :]                 # token CLS
            return torch.nn.functional.normalize(v, dim=1).cpu().numpy().astype("float32")

    print(f"kodowanie {tag} na {dev} — to jest długi krok" + (" (na CPU liczone w godzinach)" if dev == "cpu" else ""))
    t0 = time.time(); out = []
    for i in range(0, N, bs):
        out.append(enc(texts[i:i + bs]))
        if (i // bs) % 50 == 0:
            done = i + bs
            print(f"  {min(done,N)}/{N}  ETA {(N-done)/max(done/(time.time()-t0),1e-9)/60:.1f} min", flush=True)
    E = np.vstack(out)
    build[{"minilm": "MiniLM", "specter2": "SPECTER2"}[tag]] = time.time() - t0
    np.save(cache, E)
    return E

if not args.skip_semantic:
    for tag, label in [("minilm", "MiniLM"), ("specter2", "SPECTER2")]:
        E = encode_corpus(tag)
        def mk(E, mode):
            if mode == "mean":
                def f(profile, k, exclude):
                    v = E[sorted(profile)].mean(axis=0); v /= (np.linalg.norm(v) + 1e-9)
                    return _rank(E @ v, k, exclude)
            else:
                def f(profile, k, exclude):
                    return _rank((E @ E[sorted(profile)].T).max(axis=1), k, exclude)
            return f
        ENGINES[f"{label}-mean"] = mk(E, "mean")
        ENGINES[f"{label}-maxsim"] = mk(E, "maxsim")

# ────────────────────────────────────────────────────────────── 7. ewaluacja
def ndcg(hits, k, n_gt):
    dcg = sum(1 / math.log2(i + 2) for i, h in enumerate(hits[:k]) if h)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(n_gt, k))) or 1.0
    return dcg / idcg

def evaluate(name, rec_fn):
    rows, t = [], time.time()
    for u in users:
        rec = list(rec_fn(u["_profile"], max(KS), u["_profile"]))
        hits = [1 if d in u["_gt"] else 0 for d in rec]
        row = {"reader": u["user_id"]}
        for k in KS:
            row[f"P@{k}"] = sum(hits[:k]) / k
            row[f"R@{k}"] = sum(hits[:k]) / max(len(u["_gt"]), 1)
            row[f"NDCG@{k}"] = ndcg(hits, k, len(u["_gt"]))
        rows.append(row)
    d = pd.DataFrame(rows); d["engine"] = name
    return d, time.time() - t

detail = {}
for name, fn in ENGINES.items():
    detail[name], qtime[name] = evaluate(name, fn)
    print(f"{name:18} NDCG@10 = {detail[name]['NDCG@10'].mean():.4f}")

names = list(ENGINES)
summary = (pd.concat(detail[n] for n in names).groupby("engine").mean(numeric_only=True)
           .loc[names][["P@5", "P@10", "R@5", "R@10", "NDCG@5", "NDCG@10"]])

# ─────────────────────────────────────────── 8. istotność (Wilcoxon + Holm)
from scipy.stats import wilcoxon
nd = {n: detail[n].set_index("reader")["NDCG@10"] for n in names}
candidates = [("SPECTER2-maxsim", "TF-IDF"), ("MiniLM-maxsim", "TF-IDF"),
              ("SPECTER2-maxsim", "MiniLM-maxsim"), ("SPECTER2-maxsim", "SPECTER2-mean"),
              ("MiniLM-maxsim", "MiniLM-mean"), ("TF-IDF", "BM25"),
              ("TF-IDF", "Popularity"), ("BM25", "Popularity")]
rows = []
for a, bb in [(a, bb) for a, bb in candidates if a in nd and bb in nd]:
    d = nd[a] - nd[bb]
    if (d == 0).all():
        rows.append({"A": a, "B": bb, "W": np.nan, "p": 1.0, "r": 0.0, "mediana_różnicy": 0.0}); continue
    st = wilcoxon(nd[a], nd[bb]); n_eff = int((d != 0).sum())
    z = abs(st.statistic - n_eff * (n_eff + 1) / 4) / math.sqrt(n_eff * (n_eff + 1) * (2 * n_eff + 1) / 24)
    rows.append({"A": a, "B": bb, "W": st.statistic, "p": st.pvalue,
                 "r": z / math.sqrt(n_eff), "mediana_różnicy": float(np.median(d))})
sig = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
m = len(sig)
sig["p_holm"] = np.maximum.accumulate(np.minimum(1.0, sig["p"] * (m - np.arange(m))))

cost = pd.DataFrame({"silnik": list(build), "budowa indeksu [s]": [build[k] for k in build],
                     "62 zapytania [s]": [qtime.get(k, qtime.get(f"{k}-maxsim", np.nan)) for k in build]})

# ────────────────────────────────────────────────────────────── 9. zapis
summary.to_csv(f"{DATA}/results_summary.csv")
pd.concat(detail[n] for n in names).to_csv(f"{DATA}/results_per_reader.csv", index=False)
sig.to_csv(f"{DATA}/results_significance.csv", index=False)
cost.to_csv(f"{DATA}/results_cost.csv", index=False)

print("\n=== WYNIKI ===");        print(summary.round(4).to_string())
print(f"\n=== ISTOTNOŚĆ (Wilcoxon parowany, korekta Holma, rodzina {m} porównań) ===")
print(sig.round(5).to_string(index=False))
print("\n=== KOSZT (0 s = wczytano z cache, nie pomiar) ===")
print(cost.round(2).to_string(index=False))
print(f"\nzapisano 4 pliki CSV w {DATA}/")
