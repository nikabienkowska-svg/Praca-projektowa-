# Porównanie skuteczności modeli rekomendacyjnych — artykuły naukowe



Projekt PBL, temat 3: *Analiza preferencji użytkowników — system rekomendacji literatury naukowej*.

W pełni odtwarzalny pipeline porównujący treściowe systemy rekomendacji artykułów naukowych:
podejście **leksykalne** (TF-IDF, BM25) oraz **semantyczne** w dwóch odmianach — model ogólnego
przeznaczenia (`all-MiniLM-L6-v2`) i model dziedzinowy trenowany na grafie cytowań prac naukowych
(`SPECTER2`). Biblioteka: 36 314 artykułów z arXiv, 62 syntetycznych czytelników, 8 wariantów silników[cite: 2, 4].

**Żadna liczba w tym README nie jest przepisana ręcznie** — wszystkie pochodzą z plików CSV
wygenerowanych przez pipeline.

---

## Pytanie badawcze i hipotezy

> Czy semantyczna reprezentacja tekstu daje trafniejsze rekomendacje artykułów naukowych niż
> klasyczna reprezentacja leksykalna, i jakim kosztem obliczeniowym?
> 
> 

|  | hipoteza | weryfikacja |
| --- | --- | --- |
| **H1** | Model semantyczny generuje trafniejsze rekomendacje niż leksykalny.

 | ❌ **Odrzucona**[cite: 10, 12] |
| **H2** | Podejście leksykalne jest istotnie tańsze obliczeniowo.

 | **Potwierdzona**[cite: 10, 12] |
| **H3** | Oba podejścia istotnie przewyższają rekomendację niespersonalizowaną.

 | **Potwierdzona**[cite: 10, 12] |

H1 rozbito na trzy pytania rozstrzygane osobno, bo w wersji ogólnej jest niefalsyfikowalna:

1. Czy wygrywa model **ogólny** (MiniLM vs TF-IDF)? **Nie** (TF-IDF 0,321 vs MiniLM-maxsim 0,253; $p_{holm} = 0,018$)[cite: 4, 10].


2. Czy zmienia to model **dziedzinowy** (SPECTER2 vs TF-IDF)? **Nie** (TF-IDF 0,321 vs SPECTER2-maxsim 0,259; $p_{holm} = 0,030$, a SPECTER2 vs MiniLM: $p_{holm} = 0,608$)[cite: 4, 10].


3. Ile z różnicy wynika ze sposobu **budowania profilu** (max-sim vs mean)? **Bardzo dużo** — dla SPECTER2 skok z 0,146 do 0,259 ($r = 0,503$, $p_{holm} = 0,001$)[cite: 4, 10].



## Uczciwa ewaluacja — dlaczego to nie jest błędne koło

Klucz odpowiedzi nie może powstać metodą, którą się ocenia. Zbiór relewantny czytelnika to
wszystkie artykuły spełniające jego regułę współczłonkostwa kategorii arXiv
(`q-bio.NC AND drugie pole`), pomniejszone o artykuły startowe. **Kategorie są metadanymi
przypisanymi przez autorów prac — żaden z porównywanych modeli ich nie widzi**, wszystkie dostają
wyłącznie tytuł i abstrakt.

## Dane

| plik | zawartość |
| --- | --- |
| `data/corpus.jsonl.gz` | **36 314** artykułów: id, tytuł, abstrakt, kategorie[cite: 2, 4] |
| `data/users.json` | **62** profile syntetycznych czytelników, po 8 artykułów startowych[cite: 2, 4] |
| `corpus_meta.json` | procedura budowy korpusu z pełnego zrzutu arXiv (5,22 GB) + reguła zakresu[cite: 2, 7] |

Korpus zbudowano z publicznego zrzutu metadanych arXiv przez zawężenie nadzbioru
`q-bio.NC` + `cs.AI` + `cs.NE` (195 149 prac) regułą: cała kategoria `q-bio.NC` jako kręgosłup
plus prace z `cs.AI`/`cs.NE` zaklasyfikowane skrośnie do `q-bio*` albo pasujące do zestawu słów
kluczowych z neuronauki.

**Uwaga do opisu.** Rozkład kategorii jest silnie nierównomierny: `cs.AI` — 22 403 (61,7%),
`q-bio.NC` — 11 902 (32,8%), `cs.NE` — 5 666 (15,6%). Nie jest to więc korpus „neurobiologiczny",
tylko przekrój arXiv, w którym profile czytelników są zakotwiczone w `q-bio.NC`.

## Struktura repozytorium

```
corpus_meta.json               udokumentowana procedura budowy korpusu[cite: 2]
recommender_pipeline.ipynb     pełny pipeline + interfejs Gradio (wersja notebookowa)[cite: 2]
run_pipeline.py                ten sam pipeline jako skrypt (bez notebooka i internetu)[cite: 2]
eda.py                         eksploracja, kontrola jakości, SVD, wykresy do raportów 3 i 4[cite: 2]
requirements.txt               zależności[cite: 2]
RAPORTY/                       raporty etapowe 1–8 + raport końcowy[cite: 2]
data/results_summary.csv        (generowane) średnie metryki per silnik[cite: 2]
data/results_per_reader.csv     (generowane) metryki per czytelnik[cite: 2]
data/results_significance.csv   (generowane) Wilcoxon z korektą Holma[cite: 2]
data/results_cost.csv           (generowane) czasy budowy indeksu i zapytań[cite: 2]
data/results_truncation.csv     (generowane) ile tekstu widzi każdy model[cite: 2]
data/emb_*.npy                  (generowane) cache zanurzeń — drugie uruchomienie nie wymaga GPU[cite: 2]
data/fig_*.png                  (generowane) wykresy do raportu[cite: 2]

```

## Jak uruchomić

### Wariant 1 — Colab (zalecany, ok. 6 min na GPU)

1. Otwórz `recommender_pipeline.ipynb` w Google Colab (kliknij badge na samej górze)[cite: 2, 6].
2. **Środowisko wykonawcze → Zmień typ środowiska wykonawczego → T4 GPU**[cite: 1, 2].
3. Uruchom wszystko[cite: 1, 2]. Dane pobiorą się samodzielnie.



Ostatnia komórka uruchamia interfejs Gradio z podglądem rekomendacji, tabelą wyników i testami statystycznymi — to jest demo na obronę[cite: 2, 5].

### Wariant 2 — lokalnie, skryptem

```bash
pip install -r requirements.txt
python3 run_pipeline.py                  # pełny, z modelami semantycznymi[cite: 2]
python3 run_pipeline.py --skip-semantic  # tylko leksykalne, kilkadziesiąt sekund[cite: 2]

```

Na CPU kodowanie modelami semantycznymi trwa godzinami — dlatego zanurzenia są buforowane
w `data/emb_*.npy` i wystarczy je policzyć raz.

## Wyniki

Zobacz `data/results_summary.csv` (średnie metryki), `data/results_significance.csv` (testy
istotności) i `RAPORTY/Raport_7_wyniki_i_analiza_bledow.md` (omówienie).

Metryką wiodącą jest **NDCG@10**, a nie Recall — liczność kluczy odpowiedzi waha się od 12 do
1 918 artykułów (stosunek 160:1), więc Recall@10 jest dla największych ograniczony od góry
przez ok. 0,005 i nie pozwala porównywać czytelników między sobą. NDCG normalizuje przez
`min(|GT|, K)`, więc ranking idealny daje 1 niezależnie od wielkości klucza.

| silnik | typ | P@5 | P@10 | R@10 | NDCG@5 | **NDCG@10** |
| --- | --- | --- | --- | --- | --- | --- |
| Random | baseline | 0,010[cite: 4] | 0,010[cite: 4] | 0,000[cite: 4] | 0,012[cite: 4] | **0,011**[cite: 4] |
| Popularity | baseline | 0,071[cite: 4] | 0,068[cite: 4] | 0,001[cite: 4] | 0,073[cite: 4] | **0,070**[cite: 4] |
| SPECTER2-mean | semantyczny (dziedzinowy) | 0,145[cite: 4] | 0,143[cite: 4] | 0,018[cite: 4] | 0,147[cite: 4] | **0,146**[cite: 4] |
| MiniLM-mean | semantyczny (ogólny) | 0,203[cite: 4] | 0,195[cite: 4] | 0,024[cite: 4] | 0,202[cite: 4] | **0,197**[cite: 4] |
| MiniLM-maxsim | semantyczny (ogólny) | 0,271[cite: 4] | 0,231[cite: 4] | 0,037[cite: 4] | 0,286[cite: 4] | **0,253**[cite: 4] |
| SPECTER2-maxsim | semantyczny (dziedzinowy) | 0,297[cite: 4] | 0,224[cite: 4] | 0,036[cite: 4] | 0,318[cite: 4] | **0,259**[cite: 4] |
| BM25 | leksykalny | 0,290[cite: 4] | 0,235[cite: 4] | 0,034[cite: 4] | 0,313[cite: 4] | **0,267**[cite: 4] |
| **TF-IDF** | leksykalny | **0,339**[cite: 4] | **0,277**[cite: 4] | **0,039**[cite: 4] | **0,375**[cite: 4] | **0,321**[cite: 4] |

### Istotność statystyczna (Wilcoxon parowany, korekta Holma na 8 porównań)

| porównanie | mediana różnicy | $p_{holm}$ | efekt $r$ | wniosek |
| --- | --- | --- | --- | --- |
| TF-IDF vs Popularity | +0,252[cite: 4] | <0,001[cite: 4, 10] | 0,714[cite: 4] | TF-IDF istotnie lepszy[cite: 10] |
| BM25 vs Popularity | +0,187[cite: 4] | <0,001[cite: 4, 10] | 0,681[cite: 4] | BM25 istotnie lepszy[cite: 10] |
| SPECTER2-maxsim vs SPECTER2-mean | +0,116[cite: 4] | 0,001[cite: 4, 10] | 0,503[cite: 4] | max-sim istotnie lepszy[cite: 10] |
| TF-IDF vs BM25 | +0,071[cite: 4] | 0,009[cite: 4] | 0,427[cite: 4] | TF-IDF istotnie lepszy[cite: 10] |
| MiniLM-maxsim vs TF-IDF | -0,068[cite: 4] | 0,018[cite: 4] | 0,373[cite: 4] | TF-IDF istotnie lepszy[cite: 10] |
| SPECTER2-maxsim vs TF-IDF | -0,046[cite: 4] | 0,030[cite: 4] | 0,347[cite: 4] | TF-IDF istotnie lepszy[cite: 10] |
| MiniLM-maxsim vs MiniLM-mean | +0,044[cite: 4] | 0,170[cite: 4] | 0,234[cite: 4] | brak istotnej różnicy[cite: 10] |
| SPECTER2-maxsim vs MiniLM-maxsim | 0,000[cite: 4] | 0,608[cite: 4] | 0,070[cite: 4] | brak istotnej różnicy[cite: 10] |

## Ograniczenia — co wolno, a czego nie wolno wnioskować

Są istotniejsze niż same liczby.

1. **Klucz kategorialny sprzyja modelom leksykalnym.** Kategorie arXiv mocno korelują z żargonem
(`optics`, `quantum`, `spiking`, `fMRI`), więc wykrycie reguły `q-bio.NC AND physics.optics`
jest w dużej mierze zadaniem dopasowania słów. Ewentualna przewaga leksyki jest prawdziwa
**dla tego zadania i tej definicji trafności** i nie uogólnia się na wyszukiwanie semantyczne
jako takie.


2. **Warunki nie są symetryczne.** TF-IDF jest dostrojony (`min_df`, `max_df`, bigramy,
`sublinear_tf`, 50 tys. cech), oba modele semantyczne działają bez dostrajania.


3. **MiniLM nie czyta całego abstraktu.** Limit modelu to 256 word-pieces, mediana długości tekstu
w korpusie to 266 — **54,6% abstraktów przekracza limit**, model widzi 86,5% treści. SPECTER2
z limitem 512 obcina 0,1% i widzi 100%. Silniki leksykalne czytają 100%.


4. **Czytelnicy są syntetyczni.** W danych nie ma ani jednej rzeczywistej interakcji użytkownika.


5. **„Popularity" nie jest popularnością** w sensie systemów rekomendacyjnych — to proxy
centralności tematycznej, bo interakcji brak.



## Historia poprawek

Wcześniejsza wersja projektu raportowała NDCG@10 = 0,160 dla TF-IDF i 0,082 dla MiniLM.
Różnica względem obecnych wyników **nie wynika ze zmiany modelu, tylko z naprawy pomiaru**:

* **Klucz odpowiedzi był obcinany do 60 pozycji** (`gt_cap`), podczas gdy zbiory relewantne sięgają
1 918 artykułów — **36 z 62 czytelników** miało ucięty klucz, a trafienie w faktycznie relewantny
artykuł spoza tych 60 liczyło się jako pomyłka. Klucz jest teraz odtwarzany z reguły kategorii
dla całego korpusu, a rekonstrukcja weryfikowana asercją względem `n_relevant_total`.


* **Dodano BM25** — Random i Popularity leżą tak nisko, że ich pobicie niczego nie dowodziło.


* **Dodano drugą agregację profilu** (`max-sim` obok `mean`), żeby rozstrzygnąć, czy model
przegrywa jako model, czy jako sposób budowy profilu z ośmiu artykułów startowych.


* **Dodano SPECTER2** — model trenowany na grafie cytowań prac naukowych, czyli na dokładnie tej
relacji, którą projekt modeluje.


* **Poprawiono statystykę** — korekta Holma na porównania wielokrotne i wielkość efektu obok
p-value.


* **Poprawiono liczebności korpusu w opisie danych** — wcześniejsza wersja podawała
`cs.AI = 15 120` przy realnych 22 403 w korpusie.


* **Naprawiono ścieżki do danych** i **dopisano zapowiadany interfejs Gradio**.


* **Dodano `run_pipeline.py**` — wersję skryptową, uruchamialną bez notebooka i bez internetu.


* **Dodano `eda.py**` — eksplorację i kontrolę jakości danych, z których dotąd nie było śladu w kodzie.



## Technologie

Python (NumPy, pandas, SciPy, Matplotlib) · scikit-learn · Transformers / Sentence-Transformers ·
adapters (SPECTER2) · Gradio · Jupyter / Google Colab
