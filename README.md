# Praca-projektowa
# 🧠 Porównanie skuteczności modeli rekomendacyjnych (Artykuły Naukowe)

Ten projekt to w 100% odtwarzalny rurociąg analityczny (pipeline), którego celem jest porównanie skuteczności dwóch systemów rekomendacji artykułów naukowych opartych na treści (Content-Based Filtering). 

Projekt zestawia klasyczne, leksykalne podejście (**TF-IDF**) z nowoczesnym, semantycznym modelem opartym na sieciach neuronowych (**Sentence-Transformers: MiniLM**).

## 🎯 Główne cele projektu
1. **Weryfikacja Hipotezy 1 (H1):** Sprawdzenie, czy model semantyczny (MiniLM) generuje trafniejsze rekomendacje niż model leksykalny (TF-IDF).
2. **Weryfikacja Hipotezy 2 (H2):** Ocena kosztów i czasu obliczeniowego obu modeli.
3. **Uczciwa Ewaluacja (Honest Pipeline):** Stworzenie środowiska testowego, w którym modele oceniające artykuły na podstawie tytułów i abstraktów **nie mają dostępu** do ukrytych kategorii (stanowiących *ground truth*), co eliminuje problem błędnego koła w ocenianiu.

## 📊 Zbiór danych
Baza danych została wyodrębniona z publicznego zrzutu platformy **arXiv**.
* `corpus.jsonl.gz`: Biblioteka docelowa zawierająca **36 314** artykułów z dziedziny neurobiologii i kognitywistyki (q-bio.NC, cs.AI, cs.NE).
* `users.json`: Zbiór **62** profili "syntetycznych czytelników" wraz z ich historią czytania oraz ukrytym kluczem odpowiedzi.

## 🏆 Wyniki i Wnioski
Zaskakująco, nowocześniejszy model poległ w starciu z klasyką:
* **Skuteczność (H1 odrzucona):** Model **TF-IDF pokonał MiniLM**. Średnia wartość NDCG@10 dla TF-IDF wyniosła `0.158`, podczas gdy dla MiniLM tylko `0.082`. Przeprowadzony test statystyczny Wilcoxona potwierdził istotność tej różnicy.
* **Wydajność (H2 potwierdzona):** TF-IDF okazał się znacznie szybszy i tańszy w użyciu. Budowa indeksu zajęła ok. 33 sekundy (na CPU), podczas gdy kodowanie MiniLM zajęło ok. 120 sekund (i to przy wykorzystaniu akceleratora GPU).

## 🚀 Jak uruchomić projekt
Najprostszym sposobem na uruchomienie projektu jest wykorzystanie środowiska **Google Colab**.

1. Otwórz notatnik `.ipynb` w Google Colab.
2. W górnym menu wybierz `Środowisko wykonawcze` -> `Zmień typ środowiska wykonawczego` i ustaw akcelerator sprzętowy na **T4 GPU** (wymagane dla modelu MiniLM).
3. Uruchom wszystkie komórki od góry do dołu. Skrypt automatycznie pobierze dane z tego repozytorium, zainstaluje biblioteki, przeprowadzi testy i wygeneruje raporty CSV.

### 🌐 Interfejs Webowy (Gradio)
Na samym końcu notatnika znajduje się kod uruchamiający aplikację webową za pomocą biblioteki **Gradio**. Pozwala ona na interaktywne testowanie wybranego czytelnika – po wskazaniu profilu, system w czasie rzeczywistym generuje 5 rekomendacji wraz z bezpośrednimi linkami do czytelni arXiv.

## 🛠️ Wykorzystane technologie
* **Python** (Pandas, Numpy, Scipy)
* **Scikit-learn** (TfidfVectorizer)
* **Sentence-Transformers** (all-MiniLM-L6-v2)
* **Gradio** (Web UI)
* **Google Colab** (Środowisko i GPU)
