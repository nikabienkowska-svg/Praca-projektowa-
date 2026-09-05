# Raport 3 — Wczytanie, eksploracja i czyszczenie danych
**Etap:** zajęcia 5–6

Wszystkie liczby w tym raporcie pochodzą ze skryptu `eda.py`, który zapisuje wynik do
`out/eda_report.json`. Żadna nie jest przepisana ręcznie.

---

## 1. Cel etapu

Wczytanie zbioru, eksploracja jego rozkładów, kontrola typów zmiennych i braków danych oraz
podstawowa analiza statystyczna. Efektem ma być rozpoznany zbiór i decyzja, czego wymaga
czyszczenie.

## 2. Wykonane działania

- Strumieniowe wczytanie `corpus.jsonl.gz` (36 314 rekordów) bez rozpakowywania na dysk.
- Kontrola kompletności: braki w każdym z czterech pól.
- Kontrola unikalności: duplikaty identyfikatorów, duplikaty tytułów, duplikaty pełnej treści
  (skrót MD5 z tytułu i abstraktu po sprowadzeniu do małych liter).
- Analiza rozkładu długości tytułów i abstraktów.
- Analiza rozkładu kategorii i liczby kategorii przypadających na pracę.
- Analiza liczebności zbiorów relewantnych 62 czytelników.
- Decyzje o czyszczeniu i normalizacji tekstu.

## 3. Uzyskane rezultaty

### Typy zmiennych

Zbiór ma cztery pola, wszystkie tekstowe. **Nie ma zmiennych liczbowych** — więc standaryzacja
i skalowanie w klasycznym sensie nie mają tu zastosowania. Odpowiednikiem normalizacji jest
przetwarzanie tekstu na reprezentację wektorową (Raport 4).

| pole | typ | rola |
|---|---|---|
| `id` | tekst | klucz główny, identyfikator arXiv |
| `title` | tekst | cecha |
| `abstract` | tekst | cecha |
| `categories` | tekst, rozdzielony spacją | **klucz odpowiedzi** — nie jest cechą, żaden model go nie widzi |

### Braki danych

| pole | braki |
|---|---|
| `title` | 0 |
| `abstract` | 0 |
| `categories` | 0 |

Zbiór nie ma braków danych. Wynika to z konstrukcji: filtr budujący korpus wymagał obecności
wszystkich czterech pól, więc rekordy niekompletne odpadły już na etapie budowy.

### Duplikaty

| kontrola | liczba |
|---|---|
| duplikaty identyfikatora | 0 |
| duplikaty pełnej treści (tytuł + abstrakt) | 2 |
| duplikaty samego tytułu | 15 |

Duplikaty treści to 0,006% zbioru. Trzynaście przypadków powtórzonego tytułu przy różnym
abstrakcie to najpewniej różne wersje tej samej pracy albo prace o tytułach ogólnych
(np. „Comment on…"). **Decyzja: nie usuwamy.** Skala jest pomijalna, a usunięcie zmieniłoby
liczności zbiorów relewantnych i wymagałoby przebudowy klucza odpowiedzi. Fakt zostaje odnotowany.

### Rozkład długości abstraktów

| statystyka | wartość [słowa] |
|---|---|
| minimum | 5 |
| 1. kwartyl | 145 |
| **mediana** | **179** |
| średnia | 179,2 |
| 3. kwartyl | 215 |
| 90. percentyl | 246 |
| maksimum | 480 |

Rozkład jest niemal symetryczny (mediana ≈ średnia), o wąskim rozstępie międzykwartylowym —
abstrakty naukowe mają narzuconą zwyczajem długość. Wykres: `fig_dlugosc_abstraktow.png`.

**Przypadki skrajne:** 18 abstraktów krótszych niż 20 słów (0,05% zbioru) i 3 dłuższe niż 400 słów.
Krótkie abstrakty to potencjalny problem — model dostaje bardzo mało sygnału. Przy 18 przypadkach
na 36 314 nie wpływa to na wynik zbiorczy, ale jest wart odnotowania w analizie błędów.

Mediana tytułu: **10 słów**.

### Rozkład kategorii

W korpusie występują **153 różne kategorie arXiv**. Liczba kategorii na pracę: mediana 2,
średnia 2,49, maksimum 9 — czyli prace w tym zbiorze są typowo interdyscyplinarne, co jest
oczekiwane przy regule zakresu opartej na klasyfikacji skrośnej.

Piętnaście najczęstszych kategorii: `fig_kategorie.png`. Rozkład jest **silnie nierównomierny** —
`cs.AI` (22 403) występuje niemal dwukrotnie częściej niż `q-bio.NC` (11 902) i czterokrotnie
częściej niż `cs.NE` (5 666), a ogon 153 kategorii schodzi do pojedynczych prac.

### Nierównowaga zbiorów relewantnych

To jest **najważniejsza obserwacja tego etapu**. Liczność zbioru relewantnego czytelnika waha się
od **20** do **1 926** artykułów, przy medianie **99**. Stosunek największego do najmniejszego
wynosi **96,3** — zbiór jest skrajnie niezbalansowany.

Konsekwencja jest bezpośrednia: metryka Recall@10 jest dla czytelnika z 1 926 relewantnymi
artykułami ograniczona od góry przez 10/1926 ≈ 0,005 — nawet ranking idealny nie da wartości
bliskiej jedności. **Dlatego metryką wiodącą w tym projekcie jest NDCG@K, a nie Recall@K**:
NDCG normalizuje przez `min(|GT|, K)`, więc idealny ranking daje 1 niezależnie od wielkości zbioru
relewantnego, i wyniki różnych czytelników stają się porównywalne. Wykres:
`fig_zbior_relewantny.png`.

### Decyzje o czyszczeniu i normalizacji tekstu

| decyzja | uzasadnienie |
|---|---|
| połączenie tytułu i abstraktu w jeden ciąg (`"tytuł. abstrakt"`) | tytuł niesie gęsty sygnał tematyczny; oddzielne ważenie byłoby dodatkowym, niepomierzonym parametrem |
| **brak stemmingu i lematyzacji** | modele semantyczne mają własne tokenizatory word-piece i lematyzacja by je zaburzyła; żeby porównanie było uczciwe, oba podejścia dostają identyczne wejście |
| usuwanie stop-słów **tylko** w silnikach leksykalnych (`stop_words="english"`) | jest to element metody TF-IDF/BM25, a nie czyszczenie danych; modele semantyczne wymagają pełnych zdań |
| brak usuwania znaków specjalnych i notacji LaTeX | wzory są sygnałem tematycznym, a nie szumem; usunięcie ich obniżyłoby rozróżnialność w matematycznych podkategoriach |
| brak dolnej granicy długości abstraktu | 18 przypadków, usuwanie zmieniałoby klucz odpowiedzi |

**Zasada nadrzędna: oba porównywane podejścia dostają dokładnie ten sam tekst wejściowy.** Każde
czyszczenie korzystne dla jednej rodziny metod, a szkodliwe dla drugiej, unieważniłoby porównanie.

## 4. Problemy i sposoby ich rozwiązania

**Problem: standardowe kroki czyszczenia z kursu (uzupełnianie braków, standaryzacja zmiennych,
kodowanie zmiennych kategorycznych) nie mają zastosowania do zbioru czysto tekstowego.**
**Rozwiązanie:** przeniesienie ciężaru na kontrolę jakości właściwą tekstom — duplikaty, długości,
przypadki skrajne — oraz na jawne udokumentowanie decyzji o normalizacji. Standaryzacja pojawia
się dopiero na poziomie reprezentacji wektorowej (normalizacja L2, Raport 4).

**Problem: czyszczenie może przechylić porównanie.** Lematyzacja pomogłaby TF-IDF i zaszkodziła
modelom semantycznym.
**Rozwiązanie:** minimalna ingerencja w tekst i identyczne wejście dla wszystkich silników.
Każde przetwarzanie specyficzne dla metody (stop-słowa, `min_df`) należy do metody, nie do
przygotowania danych, i jest raportowane przy metodzie.

**Problem: skrajna nierównowaga zbiorów relewantnych.**
**Rozwiązanie:** wybór NDCG@K jako metryki wiodącej oraz **raportowanie rozkładu wyników per
czytelnik, a nie samej średniej** — przy stosunku 96:1 średnia może być zdominowana przez kilku
czytelników.

## 5. Plan działań na kolejny etap

1. Budowa reprezentacji wektorowej TF-IDF i pomiar jej rzadkości.
2. Redukcja wymiarów (SVD) i sprawdzenie, ile składowych niesie ile wariancji.
3. Identyfikacja kluczowych cech — terminów o największej masie TF-IDF i najsilniejszych
   składowych semantycznych.
4. Wizualizacje do raportu — do Raportu 4.
