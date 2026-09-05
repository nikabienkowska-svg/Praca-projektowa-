# Porównanie skuteczności modeli rekomendacyjnych — artykuły naukowe

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nikabienkowska-svg/Praca-projektowa-/blob/main/recommender_pipeline.ipynb)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**Projekt PBL, temat 3:** *Analiza preferencji użytkowników — system rekomendacji literatury naukowej*.  

W pełni odtwarzalny pipeline porównujący treściowe systemy rekomendacji artykułów naukowych:
podejście **leksykalne** (TF-IDF, BM25) oraz **semantyczne** w dwóch odmianach — model ogólnego
przeznaczenia (`all-MiniLM-L6-v2`) i model dziedzinowy trenowany na grafie cytowań prac naukowych
(`SPECTER2`). Biblioteka: 36 314 artykułów z arXiv, 62 syntetycznych czytelników, 8 wariantów silników.

**Żadna liczba w tym README nie jest przepisana ręcznie** — wszystkie pochodzą z plików CSV
wygenerowanych przez pipeline.

---

## Pytanie badawcze i hipotezy

> *Czy semantyczna reprezentacja tekstu (modele zanurzeń zdaniowych) daje trafniejsze rekomendacje
> artykułów naukowych niż klasyczna reprezentacja leksykalna (TF-IDF, BM25), i jakim kosztem obliczeniowym?*

### Główne hipotezy badawcze

| # | Hipoteza | Status | Uzasadnienie empiryczne |
|:---:|---|:---:|---|
| **H1** | Model semantyczny generuje trafniejsze rekomendacje niż model leksykalny. | ❌ **Odrzucona** | Dostrojony TF-IDF (NDCG@10 = 0,321) istotnie przewyższył zarówno MiniLM-maxsim (0,253; $p_{holm} = 0,018$), jak i dziedzinowy SPECTER2-maxsim (0,259; $p_{holm} = 0,030$). |
| **H2** | Podejście leksykalne jest istotnie tańsze obliczeniowo (budowa indeksu i obsługa zapytań). | ✅ **Potwierdzona** | Budowa indeksu TF-IDF zajęła ~43 s, a BM25 ~13 s. Kodowanie semantyczne trwało kilkanaście minut na GPU (i wiele godzin na CPU). Obsługa 62 zapytań: leksyka < 0,5 s vs semantyka 1,6–3,1 s. |
| **H3** | Modele personalizowane istotnie przewyższają rekomendację niespersonalizowaną. | ✅ **Potwierdzona** | Wszystkie modele personalizowane bezdyskusyjnie pokonały baseline Random (0,011) oraz Popularity (0,070; $p_{holm} < 0,001$). |

### Uszczegółowienie hipotezy H1 (Trzy pytania badawcze wg wymogów projektu)

Hipoteza H1 w wersji ogólnej jest niefalsyfikowalna (przegrana jednego modelu nie dowodzi niczego o całej klasie metod), dlatego zgodnie z Raportami 1 i 8 rozbito ją na trzy pytania rozstrzygane osobno:

1. **H1.1 (Model ogólny vs leksykalny):** Czy model semantyczny ogólnego przeznaczenia bije dostrojony model leksykalny?  
   👉 **Nie.** TF-IDF (0,321) istotnie przewyższa MiniLM-maxsim (0,253), różnica statystycznie istotna: $p_{holm} = 0,018$, $r = 0,373$.
2. **H1.2 (Model dziedzinowy vs leksykalny / ogólny):** Czy zmienia to model dziedzinowy trenowany na grafie cytowań prac naukowych?  
   👉 **Nie.** TF-IDF (0,321) istotnie przewyższa SPECTER2-maxsim (0,259; $p_{holm} = 0,030$, $r = 0,347$). Jednocześnie SPECTER2 nie różni się istotnie od modelu ogólnego MiniLM ($p_{holm} = 0,608$, $r = 0,070$).
3. **H1.3 (Wpływ agregacji profilu czytelnika):** Ile z różnicy wynika ze sposobu budowania profilu użytkownika (`max-sim` vs `mean`), a nie z samego modelu?  
   👉 **Bardzo dużo.** Agregacja `max-sim` okazała się decydująca — dla SPECTER2 podniosła NDCG@10 z 0,146 do 0,259 ($p_{holm} = 0,001$, efekt $r = 0,503$, największy w całym badaniu). Uśrednianie wektorów (`mean`) rozmywało profil czytelnika (*centroid blur*).

---

## Uczciwa ewaluacja — dlaczego to nie jest błędne koło

Klucz odpowiedzi nie może powstać metodą, którą się ocenia. Zbiór relewantny czytelnika to
wszystkie artykuły spełniające jego regułę współczłonkostwa kategorii arXiv
(`q-bio.NC AND drugie pole`), pomniejszone o artykuły startowe. **Kategorie są metadanymi
przypisanymi przez autorów prac — żaden z porównywanych modeli ich nie widzi**, wszystkie dostają
wyłącznie tytuł i abstrakt.

## Dane

| Plik | Zawartość |
|---|---|
| `corpus.jsonl.gz` | **36 314** artykułów: id, tytuł, abstrakt, kategorie |
| `users.json` | **62** profile syntetycznych czytelników, po 8 artykułów startowych |
| `corpus_meta.json` | Procedura budowy korpusu z pełnego zrzutu arXiv (5,22 GB) + reguła zakresu |

Korpus zbudowano z publicznego zrzutu metadanych arXiv przez zawężenie nadzbioru
`q-bio.NC` + `cs.AI` + `cs.NE` (195 149 prac) regułą: cała kategoria `q-bio.NC` jako kręgosłup
plus prace z `cs.AI`/`cs.NE` zaklasyfikowane skrośnie do `q-bio*` albo pasujące do zestawu słów
kluczowych z neuronauki.

**Uwaga do opisu.** Rozkład kategorii jest silnie nierównomierny: `cs.AI` — 22 403 (61,7%),
`q-bio.NC` — 11 902 (32,8%), `cs.NE` — 5 666 (15,6%). Nie jest to więc korpus „neurobiologiczny",
tylko przekrój arXiv, w którym profile czytelników są zakotwiczone w `q-bio.NC`.

## Struktura repozytorium

```
corpus_meta.json               Udokumentowana procedura budowy korpusu i statystyki
corpus.jsonl.gz                Korpus 36 314 artykułów naukowych z arXiv (id, title, abstract, categories)
users.json                     62 profile syntetycznych czytelników zakotwiczonych w q-bio.NC
recommender_pipeline.ipynb     Pełny pipeline badawczy + interfejs Gradio (wersja Google Colab)
run_pipeline.py                Ten sam pipeline jako skrypt konsolowy (uruchamialny offline)
eda.py                         Eksploracja, kontrola jakości, SVD, wykresy do raportów 3 i 4
make_users.py                  Generator profili syntetycznych czytelników
build_corpus.py                Generator korpusu z surowego zrzutu arXiv
requirements.txt               Zależności środowiska Python
RAPORTY/                       Komplet 8 raportów etapowych projektu (Raporty 1–8)
RAPORT_KONCOWY.md              Raport końcowy integrujący całość badań
results_summary.csv            Średnie metryki ewaluacji (P@K, R@K, NDCG@K)
results_per_reader.csv         Szczegółowe metryki ewaluacji per czytelnik (496 rekordów)
results_significance.csv       Wyniki parowanego testu Wilcoxona z korektą Holma
results_cost.csv               Czasy budowy indeksu oraz obsługi 62 zapytań
```

## Jak uruchomić

### Wariant 1 — Colab (zalecany, ok. 6 min na GPU)

👉 **[Otwórz `recommender_pipeline.ipynb` bezpośrednio w Google Colab](https://colab.research.google.com/github/nikabienkowska-svg/Praca-projektowa-/blob/main/recommender_pipeline.ipynb)** (lub kliknij plakietkę na górze strony).

1. W menu Colaba wybierz: **Środowisko wykonawcze → Zmień typ środowiska wykonawczego → T4 GPU** (zalecane, by kodowanie semantyczne zajęło ~6 minut zamiast wielu godzin na CPU).
2. Wybierz: **Środowisko wykonawcze → Uruchom wszystko**. Dane korpusu pobiorą się automatycznie z repozytorium.
3. Ostatnia komórka uruchamia interaktywny interfejs demonstracyjny **Gradio** z podglądem rekomendacji, tabelą metryk i testami statystycznymi (narzędzie do prezentacji na obronie).

### Wariant 2 — lokalnie, skryptem

```bash
pip install -r requirements.txt
python3 run_pipeline.py                  # pełny, z modelami semantycznymi
python3 run_pipeline.py --skip-semantic  # tylko leksykalne, kilkadziesiąt sekund
```

Na CPU kodowanie modelami semantycznymi trwa godzinami — dlatego zanurzenia są buforowane
w `data/emb_*.npy` i wystarczy je policzyć raz.

## Wyniki

Zobacz `results_summary.csv` (średnie metryki), `results_significance.csv` (testy istotności)
oraz [Raport 7 — Wyniki i analiza błędów](RAPORTY/Raport_7_wyniki_i_analiza_bledow.md).

Metryką wiodącą jest **NDCG@10**, a nie Recall — liczność kluczy odpowiedzi waha się od 12 do
1 918 artykułów (stosunek 160:1), więc Recall@10 jest dla największych ograniczony od góry
przez ok. 0,005 i nie pozwala porównywać czytelników między sobą. NDCG normalizuje przez
`min(|GT|, K)`, więc ranking idealny daje 1 niezależnie od wielkości klucza.

| Silnik | Typ | P@5 | P@10 | R@10 | NDCG@5 | **NDCG@10** |
|---|---|:---:|:---:|:---:|:---:|:---:|
| Random | baseline | 0,010 | 0,010 | 0,000 | 0,012 | **0,011** |
| Popularity | baseline | 0,071 | 0,068 | 0,001 | 0,073 | **0,070** |
| SPECTER2-mean | semantyczny (dziedzinowy) | 0,145 | 0,143 | 0,018 | 0,147 | **0,146** |
| MiniLM-mean | semantyczny (ogólny) | 0,203 | 0,195 | 0,024 | 0,202 | **0,197** |
| MiniLM-maxsim | semantyczny (ogólny) | 0,271 | 0,231 | 0,037 | 0,286 | **0,253** |
| SPECTER2-maxsim | semantyczny (dziedzinowy) | 0,297 | 0,224 | 0,036 | 0,318 | **0,259** |
| BM25 | leksykalny | 0,290 | 0,235 | 0,034 | 0,313 | **0,267** |
| **TF-IDF** | leksykalny | **0,339** | **0,277** | **0,039** | **0,375** | **0,321** |

### Istotność statystyczna (Wilcoxon parowany, korekta Holma na 8 porównań)

| Porównanie | Mediana różnicy | $p_{holm}$ | Efekt $r$ | Wniosek |
|---|:---:|:---:|:---:|---|
| TF-IDF vs Popularity | +0,252 | <0,001 | 0,714 | TF-IDF istotnie lepszy |
| BM25 vs Popularity | +0,187 | <0,001 | 0,681 | BM25 istotnie lepszy |
| SPECTER2-maxsim vs SPECTER2-mean | +0,116 | 0,001 | 0,503 | max-sim istotnie lepszy |
| TF-IDF vs BM25 | +0,071 | 0,009 | 0,427 | TF-IDF istotnie lepszy |
| MiniLM-maxsim vs TF-IDF | -0,068 | 0,018 | 0,373 | TF-IDF istotnie lepszy |
| SPECTER2-maxsim vs TF-IDF | -0,046 | 0,030 | 0,347 | TF-IDF istotnie lepszy |
| MiniLM-maxsim vs MiniLM-mean | +0,044 | 0,170 | 0,234 | brak istotnej różnicy |
| SPECTER2-maxsim vs MiniLM-maxsim | 0,000 | 0,608 | 0,070 | brak istotnej różnicy |

---

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

---

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
* **Naprawiono ścieżki do danych** i **dopisano interfejs demonstracyjny Gradio**.
* **Dodano `run_pipeline.py`** — wersję skryptową, uruchamialną bez notebooka i bez internetu.
* **Dodano `eda.py`** — eksplorację i kontrolę jakości danych, z których dotąd nie było śladu w kodzie.

---

## Technologie

Python (NumPy, pandas, SciPy, Matplotlib) · scikit-learn · Transformers / Sentence-Transformers ·
adapters (SPECTER2) · Gradio · Jupyter / Google Colab
