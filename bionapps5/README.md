# FOSSA2

Repozytorium służy do składowania kodu podprojektu FOSSA2 w ramach BION-B

## Spis Treści

*   [Informacje o projekcie](##Informacje-o-projekcie)
*   [Zasady pracy z kodem w repozytorium](##Zasady-pracy-z-kodem-w-repozytorium)


## Informacje o projekcie

|Rola|e-mail|
|---|---|
|Maintainer:|olaf.michalski@knf.gov.pl|
|Dokumentacja:|https://confluence.knf.gov.pl/pages/viewpage.action?pageId=58526161 |

## Zasady pracy z kodem w repozytorium

*   Kod musi posiadać wskazaną wersję, zgodnie z formatem https://semver.org/.
*   Kod musi posiadać listę wszystkich wymagań i zależności (biblioteki, frameworki, pliki konfiguracyjne etc.).
*   Kod musi posiadać pełną instrukcję uruchomienia od pobrania kodu z repozytorium do uzyskania działającej aplikacji.
*   Wszystkie *commit messages* muszą opisywać zawartość danej porcji kodu i być zgodne z nazwą Issue w GitLab
*   Nazwa *brancha* utworzonego na podstawie *Issue* musi zawierać numer issue, przykładowo: ```123-paczka-wersja-1.7.1``` (GitLab ułatwia to automatycznie tworząc branch i podstawiając pod ten wzór stosowny numer, gdy skorzysta się z opcji *Create Merge Request* w *Issue*).
*   W miarę możliwości nalezy unikać umieszczania w repozytorium plików binarnych, ponieważ utrudnia to kontrolę wersji.
*   Kod musi być przygotowany do umieszczenia w repozytorium w sposób zgodny ze standardami kodowania w danym języku / frameworku, przykładowo niedozwolone jest submitowanie kodu Python wraz z plikami venv, plików cache niesłużących do zbudowania lub uruchomienia aplikacji, plików framework-ów frontendowych niesłużacych do obsługi aplikacji (np. wybranych submodules), etc.

## Proces umieszczania kodu w repozytorium

*   Maintainer otwiera *Issue* z porcją kodu i przypisuje go do konkretnej osoby po stronie Deweloperów
*   Deweloper otwiera *Merge Request* na podstawie w/w *Issue* z zachowaniem wszystkich zasad wymienionych w sekcji [Zasady umieszczania kodu w repozytorium](#Zasady-umieszczania-kodu-w-repozytorium).
*   Deweloper tworzy commit z paczką kodu i wystawia go na repozytorium zdalne, po czym informuje w dowolny sposób Maintainera o zmianach (na kanale Teams w wątku Code Review).
*   Maintainer wykonuje *Code Review*, sprawdza zachowanie Zasad oraz poprawność kodu: w razie potrzeby umieszcza uwagi dla Wykonawcy.
*   Po zakończeniu Code Review Maintainer wykonujący merge-a taguje daną gałąź za pomocą komendy:
```git tag x.x.x```
*   W razie potrzeby aktualizowana jest instrukcja uruchomieniowa w README.md oraz dokumentacja projektu
*   Maintainer dokonuje merge-a *feature_branch* -> *main*
*   Maintainer aktualizuje ```CHANGELOG.md```
*   Maintainer zamyka *Issue* związane z MR

![screenshot](./repo_resources/repo_process.png)

## Instrukcja uruchomieniowa

### Zainstalowanie zależności
```
pip install -r .\requirements.txt
```

### Start projektu
```
django-admin startproject bionbapps
```

### Przeprowadzenie migracji
```
cd  bionbapps
python .\manage.py migrate
```

### uruchomienie serwera programistycznego
```
python .\manage.py runserver
```

### Stworzenie aplikacji w pakiecie (onbecnie jedynie fossa2)
```
python .\manage.py startapp fossa2
```

### Ponowne migracje po pracy z modelami
```
python .\manage.py makemigrations
python .\manage.py migrate
```

### Stworzenie superuser-a

```
python manage.py createsuperuser

Username (leave blank to use 'micho'): admin
Email address: admin@bionapps.pl
Password: BIONApp!@_12??
```