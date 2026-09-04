# Porównanie skuteczności modeli rekomendacyjnych — artykuły naukowe

Projekt PBL, temat 3: *Analiza preferencji użytkowników — system rekomendacji literatury naukowej*.

W pełni odtwarzalny pipeline porównujący treściowe systemy rekomendacji artykułów naukowych:
podejście **leksykalne** (TF-IDF, BM25) oraz **semantyczne** w dwóch odmianach — model ogólnego
przeznaczenia (`all-MiniLM-L6-v2`) i model dziedzinowy trenowany na grafie cytowań prac naukowych
(SPECTER2). Biblioteka: 36 314 artykułów z arXiv, 62 syntetycznych czytelników.

**Żadna liczba w tym README nie jest przepisana ręcznie** — wszystkie pochodzą z plików CSV
wygenerowanych przez pipeline.

---

## Pytanie badawcze i hipotezy

> Czy semantyczna reprezentacja tekstu daje trafniejsze rekomendacje artykułów naukowych niż
> klasyczna reprezentacja leksykalna, i jakim kosztem obliczeniowym?

| | hipoteza |
|---|---|
| **H1** | Model semantyczny generuje trafniejsze rekomendacje niż leksykalny. |
| **H2** | Podejście leksykalne jest istotnie tańsze obliczeniowo. |
| **H3** | Oba podejścia istotnie przewyższają rekomendację niespersonalizowaną. |

H1 rozbito na trzy pytania rozstrzygane osobno, bo w wersji ogólnej jest niefalsyfikowalna:
czy wygrywa model **ogólny** (MiniLM vs TF-IDF), czy zmienia to model **dziedzinowy**
(SPECTER2 vs TF-IDF) i ile z różnicy wynika ze sposobu **budowania profilu** (max-sim vs mean).

## Uczciwa ewaluacja — dlaczego to nie jest błędne koło

Klucz odpowiedzi nie może powstać metodą, którą się ocenia. Zbiór relewantny czytelnika to
wszystkie artykuły spełniające jego regułę współczłonkostwa kategorii arXiv
(`q-bio.NC AND drugie pole`), pomniejszone o artykuły startowe. **Kategorie są metadanymi
przypisanymi przez autorów prac — żaden z porównywanych modeli ich nie widzi**, wszystkie dostają
wyłącznie tytuł i abstrakt.

## Dane

| plik | zawartość |
|---|---|
| `corpus.jsonl.gz` | **36 314** artykułów: id, tytuł, abstrakt, kategorie |
| `users.json` | **62** profile syntetycznych czytelników, po 8 artykułów startowych |
| `corpus_meta.json` | procedura budowy korpusu z pełnego zrzutu arXiv (5,22 GB) + reguła zakresu |

Korpus zbudowano z publicznego zrzutu metadanych arXiv przez zawężenie nadzbioru
`q-bio.NC` + `cs.AI` + `cs.NE` (195 149 prac) regułą: cała kategoria `q-bio.NC` jako kręgosłup
plus prace z `cs.AI`/`cs.NE` zaklasyfikowane skrośnie do `q-bio*` albo pasujące do zestawu słów
kluczowych z neuronauki.

**Uwaga do opisu.** Rozkład kategorii jest silnie nierównomierny: `cs.AI` — 22 403 (61,7%),
`q-bio.NC` — 11 902 (32,8%), `cs.NE` — 5 666 (15,6%). Nie jest to więc korpus „neurobiologiczny",
tylko przekrój arXiv, w którym profile czytelników są zakotwiczone w `q-bio.NC`.

## Struktura repozytorium

```
corpus.jsonl.gz               dane: 36 314 artykułów
users.json                    dane: 62 profile czytelników
corpus_meta.json              udokumentowana procedura budowy korpusu
recommender_pipeline.ipynb    pełny pipeline + interfejs Gradio (wersja notebookowa)
run_pipeline.py               ten sam pipeline jako skrypt (bez notebooka i internetu)
eda.py                        eksploracja, kontrola jakości, SVD, wykresy do raportów 3 i 4
requirements.txt              zależności
RAPORTY/                      raporty etapowe 1–8 + raport końcowy
data/results_summary.csv        (generowane) średnie metryki per silnik
data/results_per_reader.csv     (generowane) metryki per czytelnik
data/results_significance.csv   (generowane) Wilcoxon z korektą Holma
data/results_cost.csv           (generowane) czasy budowy indeksu i zapytań
data/results_truncation.csv     (generowane) ile tekstu widzi każdy model
data/emb_*.npy                  (generowane) cache zanurzeń — drugie uruchomienie nie wymaga GPU
data/fig_*.png                  (generowane) wykresy do raportu
```

## Jak uruchomić

### Wariant 1 — Colab (zalecany, ok. 6 min)

1. Otwórz `Projekt_rekomendacje_program.ipynb` w Google Colab.
2. **Środowisko wykonawcze → Zmień typ → T4 GPU.**
3. Uruchom wszystko. Dane pobiorą się samodzielnie.

Ostatnia komórka uruchamia interfejs Gradio z czterema zakładkami (wyniki, istotność, widok
pojedynczego czytelnika, analiza błędów) — to jest demo na obronę.

### Wariant 2 — lokalnie, skryptem

```bash
pip install -r requirements.txt
python3 run_pipeline.py                  # pełny, z modelami semantycznymi
python3 run_pipeline.py --skip-semantic  # tylko leksykalne, kilkadziesiąt sekund
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

- **Klucz odpowiedzi był obcinany do 60 pozycji** (`gt_cap`), podczas gdy zbiory relewantne sięgają
  1 918 artykułów — **36 z 62 czytelników** miało ucięty klucz, a trafienie w faktycznie relewantny
  artykuł spoza tych 60 liczyło się jako pomyłka. Klucz jest teraz odtwarzany z reguły kategorii
  dla całego korpusu, a rekonstrukcja weryfikowana asercją względem `n_relevant_total`.
- **Dodano BM25** — Random i Popularity leżą tak nisko, że ich pobicie niczego nie dowodziło.
- **Dodano drugą agregację profilu** (`max-sim` obok `mean`), żeby rozstrzygnąć, czy model
  przegrywa jako model, czy jako sposób budowy profilu z ośmiu artykułów startowych.
- **Dodano SPECTER2** — model trenowany na grafie cytowań prac naukowych, czyli na dokładnie tej
  relacji, którą projekt modeluje.
- **Poprawiono statystykę** — korekta Holma na porównania wielokrotne i wielkość efektu obok
  p-value.
- **Poprawiono liczebności korpusu w opisie danych** — wcześniejsza wersja podawała
  `cs.AI = 15 120` przy realnych 22 403 w korpusie.
- **Naprawiono ścieżki do danych** i **dopisano zapowiadany interfejs Gradio**.
- **Dodano `run_pipeline.py`** — wersję skryptową, uruchamialną bez notebooka i bez internetu.
- **Dodano `eda.py`** — eksplorację i kontrolę jakości danych, z których dotąd nie było śladu w kodzie.

## Technologie

Python (NumPy, pandas, SciPy, Matplotlib) · scikit-learn · Transformers / Sentence-Transformers ·
adapters (SPECTER2) · Gradio · Jupyter / Google Colab
