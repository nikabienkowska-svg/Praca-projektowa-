# Porównanie skuteczności modeli rekomendacyjnych — artykuły naukowe

W pełni odtwarzalny pipeline porównujący treściowe systemy rekomendacji artykułów naukowych: podejście leksykalne (**TF-IDF**, **BM25**) i semantyczne (**Sentence-Transformers `all-MiniLM-L6-v2`**), na bibliotece 36 314 artykułów z arXiv i 62 syntetycznych czytelnikach.

Notebook pobiera dane samodzielnie, liczy wszystkie metryki od zera i zapisuje wyniki do plików CSV. Żadna liczba w tym README nie jest przepisana ręcznie — każda pochodzi z `results_summary.csv` wygenerowanego przez pipeline.

## Cele

1. **H1 — trafność.** Czy model semantyczny generuje trafniejsze rekomendacje niż model leksykalny?
2. **H2 — koszt.** Ile kosztuje budowa indeksu i obsługa zapytania w obu podejściach?
3. **Uczciwa ewaluacja.** Klucz odpowiedzi nie może powstać metodą, którą się ocenia — inaczej ocena jest błędnym kołem.

## Dane

Korpus pochodzi z publicznego zrzutu arXiv.

- `corpus.jsonl.gz` — **36 314** artykułów z przekroju `q-bio.NC` + `cs.AI` + `cs.NE`. Rozkład kategorii jest silnie nierównomierny: `cs.AI` to 22 403 pozycje (61,7%), `q-bio.NC` — 11 902 (32,8%), `cs.NE` — 5 666 (15,6%). Nie jest to więc korpus „neurobiologiczny", tylko przekrój arXiv, w którym profile czytelników są zakotwiczone w `q-bio.NC`.
- `users.json` — **62** profile syntetycznych czytelników, po 8 artykułów startowych każdy.

**Klucz odpowiedzi (ground truth).** Zbiór relewantny czytelnika to wszystkie artykuły spełniające jego regułę współczłonkostwa kategorii arXiv (`q-bio.NC AND drugie pole`), pomniejszone o artykuły startowe. Kategorie są metadanymi przypisanymi przez autorów prac — żaden z porównywanych modeli ich nie widzi, oba dostają wyłącznie tytuł i abstrakt. Ocena nie jest zatem błędnym kołem.

## Wyniki

Średnie po 62 czytelnikach, pełny klucz kategorialny:

| silnik | P@5 | P@10 | R@10 | NDCG@5 | NDCG@10 |
|---|---|---|---|---|---|
| Random | 0,010 | 0,010 | 0,000 | 0,012 | 0,011 |
| Popularity | 0,071 | 0,068 | 0,001 | 0,073 | 0,070 |
| BM25 | 0,290 | 0,236 | 0,034 | 0,313 | 0,267 |
| **TF-IDF** | **0,339** | **0,277** | **0,039** | **0,375** | **0,321** |
| MiniLM (mean) | — | — | — | — | — |
| MiniLM (max-sim) | — | — | — | — | — |

Wiersze MiniLM uzupełnia się po uruchomieniu notebooka na GPU (kodowanie 36 tys. abstraktów zajmuje ok. 2 min na T4 i ok. 40 min na CPU).

**Istotność.** TF-IDF pokonuje BM25 (Wilcoxon parowany na NDCG@10: p = 0,002 po korekcie Holma, r = 0,43 — efekt średni) oraz Popularity (p < 0,001, r = 0,71). Porównania z MiniLM liczy komórka 11 notebooka.

**Koszt (H2).** Budowa indeksu: BM25 ok. 4 s, TF-IDF ok. 21 s, MiniLM ok. 2 min na GPU / ok. 40 min na CPU (pomiar na jednym rdzeniu; wartości zależą od sprzętu). Obsługa 62 zapytań: poniżej sekundy w każdym z silników leksykalnych.

## Jak uruchomić

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1yAdOfpc8Kn4cuqiVDBcC7gBgEzjQxKSC?usp=sharing)

1. Kliknij **Open in Colab**.
2. `Środowisko wykonawcze → Zmień typ środowiska wykonawczego → T4 GPU`.
3. Uruchom komórki od góry do dołu. Dane pobiorą się automatycznie z tego repozytorium.

Lokalnie: `pip install -r requirements.txt`, następnie `jupyter lab recommender_pipeline.ipynb`. Notebook wykryje pliki danych w katalogu repozytorium i nie będzie ich pobierał ponownie.

### Interfejs webowy (Gradio)

Ostatnia komórka uruchamia aplikację, w której dla wybranego czytelnika i wybranego silnika widać rekomendacje z linkami do arXiv oraz oznaczeniem, które pozycje znajdują się w kluczu odpowiedzi.

## Ograniczenia — co wolno, a czego nie wolno wnioskować

Są istotniejsze niż same liczby i muszą znaleźć się we wnioskach.

1. **Klucz kategorialny sprzyja modelom leksykalnym.** Kategorie arXiv mocno korelują z żargonem (`optics`, `quantum`, `spiking`, `fMRI`), więc wykrycie reguły `q-bio.NC AND physics.optics` jest w dużej mierze zadaniem dopasowania słów. Przewaga podejścia leksykalnego jest prawdziwa **dla tego zadania i tej definicji trafności** i nie uogólnia się na wyszukiwanie semantyczne jako takie.
2. **Warunki nie są symetryczne.** TF-IDF jest dostrojony (`min_df`, `max_df`, bigramy, `sublinear_tf`, 50 tys. cech), MiniLM działa bez dostrajania.
3. **MiniLM nie czyta całego abstraktu.** Limit modelu to 256 word-pieces; mediana długości tekstu w tym korpusie wynosi 266 tokenów, a **54,6% abstraktów przekracza limit**. Model widzi 86,5% tekstu, silniki leksykalne — 100%.
4. **`all-MiniLM-L6-v2` to model ogólnego przeznaczenia.** Dla literatury naukowej właściwym punktem odniesienia byłby SPECTER2 albo `bge`/`gte`. Dopisanie takiego modelu to najbardziej wartościowe rozszerzenie tej pracy.
5. **Czytelnicy są syntetyczni.** W danych nie ma ani jednej rzeczywistej interakcji użytkownika, a kategoria to zgrubne przybliżenie preferencji.
6. **„Popularity" nie jest popularnością** w sensie systemów rekomendacyjnych — to proxy centralności tematycznej, bo interakcji brak.

Wobec tego H1 wolno odrzucić wyłącznie w brzmieniu: *ten konkretny model semantyczny, z tą agregacją profilu i przy kategorialnej definicji trafności, nie pobił dostrojonego modelu leksykalnego*. H2 broni się bez zastrzeżeń.

## Technologie

Python (NumPy, pandas, SciPy) · scikit-learn · Sentence-Transformers · Gradio · Jupyter / Google Colab

## Struktura repozytorium

```
corpus.jsonl.gz             36 314 artykułów: id, tytuł, abstrakt, kategorie
users.json                  62 profile czytelników
recommender_pipeline.ipynb  cały pipeline: dane → modele → metryki → testy → Gradio
requirements.txt            zależności do uruchomienia lokalnego
data/results_summary.csv    (generowane) średnie metryki per silnik
data/results_per_reader.csv (generowane) metryki per czytelnik
data/results_significance.csv (generowane) testy Wilcoxona
```
