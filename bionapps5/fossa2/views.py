import re
from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, permissions

from .models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie
from .forms import PodmiotForm, ObszarForm, BlokForm, PytanieForm, GrupaNaglowekForm, GrupaPodmiotyForm, AnkietaNaglowekForm, AnkietaPytaniaForm

from fossa2.generator import get_data_by_grupanaglowek_id, transform_dict, generuj
from django.http import JsonResponse
from .serializers import PodmiotSerializer
from fossa2.models import Blok, OkresSprawozdawczy, INFINITY_DATE

inf = date(9999, 12, 31)
class PodmiotViewSet(viewsets.ModelViewSet):
    queryset = Podmiot.objects.all().order_by('kod')
    serializer_class = PodmiotSerializer
    permission_classes = [permissions.AllowAny]
def ajax_load_bloki(request):
    # Pobieramy ID obszaru z zapytania JS
    obszar_id = request.GET.get('id_obszaru')
    bloki = Blok.objects.filter(id_obszaru_id=obszar_id,data_do=inf).order_by('kod')
    print(Blok.objects)
    print(bloki)
    data = [{'id': b.id, 'kod': b.kod, 'tresc': b.tresc[:30]} for b in bloki]
    return JsonResponse(data, safe=False)

# 2. Ładowanie Podbloków na podstawie wybranego Bloku
def ajax_load_podbloki(request):
    print("xxxxxxxxxx")
    # Pobieramy ID bloku z zapytania JS
    blok_id = request.GET.get('id_bloku')
    podbloki = Podblok.objects.filter(id_bloku_id=blok_id,data_do=inf).order_by('kod')
    print(podbloki)
    data = [{'id': p.id, 'kod': p.kod, 'tresc': p.tresc[:30]} for p in podbloki]
    return JsonResponse(data, safe=False)


def ajax_load_pytania(request):
    """Widok zwracający listę pytań przypisanych do konkretnego podbloku"""
    podblok_id = request.GET.get('id_podbloku')
    pytania = Pytanie.objects.filter(id_podbloku_id=podblok_id,data_do=inf).order_by('kod')

    # Przygotowanie danych do wysłania (id do wartości select, kod do wyświetlenia)
    data = [
        {
            'id': py.id,
            'kod': py.kod,
            'tresc': py.tresc[:40] + '...' if len(py.tresc) > 40 else py.tresc
        }
        for py in pytania
    ]
    return JsonResponse(data, safe=False)

#def home(request):
#    return render(request, 'fossa2/home.html')

def podmiot_list(request):
    # Obsługa dodawania nowego podmiotu
    if request.method == 'POST' and 'add_podmiot' in request.POST:
        form = PodmiotForm(request.POST)
        if form.is_valid():
            podmiot = form.save(commit=False)
            podmiot.utworzone_przez_uzytkownika = request.user.username
            podmiot.save()
            return redirect(request.path_info)
    else:
        form = PodmiotForm()

    # Obsługa usuwania podmiotu
    if request.method == 'POST' and 'delete_podmiot' in request.POST:
        podmiot_id = request.POST.get('podmiot_id')
        podmiot = get_object_or_404(Podmiot, id=podmiot_id)
        podmiot.delete()
        return redirect(request.path_info)

    # Pobierz parametry filtrowania z żądania
    kod_filter = request.GET.get('kod', '')
    nazwa_filter = request.GET.get('nazwa', '')

    # Filtruj dane na podstawie parametrów
    podmioty = Podmiot.objects.all()
    if kod_filter:
        podmioty = podmioty.filter(kod__icontains=kod_filter)
    if nazwa_filter:
        podmioty = podmioty.filter(nazwa__icontains=nazwa_filter)

    # Pobierz liczbę wyników na stronę z żądania
    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(podmioty, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'kod_filter': kod_filter,
        'nazwa_filter': nazwa_filter,
        'results_per_page': results_per_page,
        'form': form,
    }

    return render(request, 'fossa2/podmiot_list.html', context)

def podblok_list(request):
    return render(request, 'fossa2/podblok_list.html')
def podzapytanie_list(request):
    return render(request, 'fossa2/podzapytanie_list.html')
def obszar_list(request):
    # Obsługa dodawania nowego obszaru
    if request.method == 'POST' and 'add_obszar' in request.POST:
        form = ObszarForm(request.POST)
        if form.is_valid():
            obszar = form.save(commit=False)
            obszar.utworzone_przez_uzytkownika = request.user.username
            obszar.save()
            return redirect(request.path_info)
    else:
        form = ObszarForm()

    # Obsługa usuwania obszaru
    if request.method == 'POST' and 'delete_obszar' in request.POST:
        obszar_id = request.POST.get('obszar_id')
        obszar = get_object_or_404(Obszar, id=obszar_id)
        obszar.delete()
        return redirect(request.path_info)

    # Pobierz parametry filtrowania z żądania
    kod_filter = request.GET.get('kod', '')
    nazwa_filter = request.GET.get('nazwa', '')

    # Filtruj dane na podstawie parametrów
    obszary = Obszar.objects.all()
    if kod_filter:
        obszary = obszary.filter(kod__icontains=kod_filter)
    if nazwa_filter:
        obszary = obszary.filter(nazwa__icontains=nazwa_filter)

    # Pobierz liczbę wyników na stronę z żądania
    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(obszary, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'kod_filter': kod_filter,
        'nazwa_filter': nazwa_filter,
        'results_per_page': results_per_page,
        'form': form,
    }
    return render(request, 'fossa2/obszar_list.html', context)


def blok_list(request):
    # Obsługa dodawania nowego bloku
    if request.method == 'POST' and 'add_blok' in request.POST:
        form = BlokForm(request.POST)

        if form.is_valid():
            blok = form.save(commit=False)

            obszar = blok.id_obszaru
            ostatni = obszar.bloki.all()

            if ostatni.exists():
                ostatni_kod = max(int(b.kod) for b in ostatni)
                nowy_kod = str(ostatni_kod + 1)
            else:
                nowy_kod = '1'

            blok.kod = nowy_kod

            blok.utworzone_przez_uzytkownika = request.user.username
            blok.save()
            return redirect(request.path_info)
    else:
        form = BlokForm()

    # Obsługa usuwania bloku
    if request.method == 'POST' and 'delete_blok' in request.POST:
        blok_id = request.POST.get('blok_id')
        blok = get_object_or_404(Blok, id=blok_id)
        blok.delete()
        return redirect(request.path_info)

    # Pobierz parametry filtrowania z żądania
    obszar_filter = request.GET.get('obszar', '')
    kod_filter = request.GET.get('kod', '')
    tresc_filter = request.GET.get('tresc', '')

    # Filtruj dane na podstawie parametrów
    bloki = Blok.objects.all()
    if obszar_filter:
        bloki = bloki.filter(obszar_id_obszaru__icontains=obszar_filter)
    if kod_filter:
        bloki = bloki.filter(kod__icontains=kod_filter)
    if tresc_filter:
        bloki = bloki.filter(tresc__icontains=tresc_filter)

    # Pobierz liczbę wyników na stronę z żądania
    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(bloki, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'obszar_filter': obszar_filter,
        'kod_filter': kod_filter,
        'tresc_filter': tresc_filter,
        'results_per_page': results_per_page,
        'form': form,
    }
    return render(request, 'fossa2/blok_list.html', context)


def pytanie_list(request):
    # pytania = Pytanie.objects.all()
    pytania = Pytanie.objects.select_related('id_bloku__id_obszaru').all()

    # Filtry
    kod_filter = request.GET.get('kod', '')
    blok_filter = request.GET.get('blok', '')
    tresc_filter = request.GET.get('tresc', '')
    obligatoryjne_filter = request.GET.get('obligatoryjne', '')
    wytyczne_filter = request.GET.get('wytyczne', '')

    if kod_filter:
        pytania = pytania.filter(kod__icontains=kod_filter)
    if blok_filter:
        pytania = pytania.filter(id_bloku__kod__icontains=blok_filter)
    if tresc_filter:
        pytania = pytania.filter(tresc__icontains=tresc_filter)
    if obligatoryjne_filter:
        pytania = pytania.filter(tresc__icontains=obligatoryjne_filter)
    if wytyczne_filter:
        pytania = pytania.filter(tresc__icontains=wytyczne_filter)

    # Pobierz liczbę wyników na stronę z żądania
    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(pytania, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dodawanie nowego pytania
    if request.method == 'POST':
        form = PytanieForm(request.POST)
        if form.is_valid():
            pytanie_list = form.save(commit=False)
            pytanie_list.utworzone_przez_uzytkownika = request.user.username
            pytanie_list.save()
            return redirect('pytanie_list')
    else:
        form = PytanieForm()

    bloki = Blok.objects.select_related('id_obszaru').all()

    context = {
        'page_obj': page_obj,
        'form': form,
        'kod_filter': kod_filter,
        'blok_filter': blok_filter,
        'tresc_filter': tresc_filter,
        'obligatoryjne_filter': obligatoryjne_filter,
        'wytyczne_filter': wytyczne_filter,
        'bloki': bloki,
        'results_per_page': results_per_page,
    }

    if request.method == 'POST' and 'delete_pytanie' in request.POST:
        pytanie_id = request.POST.get('pytanie_id')
        pytanie = get_object_or_404(Pytanie, id=pytanie_id)
        pytanie.delete()
        return redirect(request.path_info)

    return render(request, 'fossa2/pytanie_list.html', context)


def grupanaglowek_list(request):

    def get_okres_context(self, request):
        okresy_wszystkie = OkresSprawozdawczy.objects.all()
        rok_param = request.GET.get('rok') or request.POST.get('rok')

        if rok_param:
            wybrany_okres = get_object_or_404(OkresSprawozdawczy, rok=int(rok_param))
        else:
            wybrany_okres = OkresSprawozdawczy.get_aktywny_rok() or okresy_wszystkie.first()

        czy_tryb_edycji = wybrany_okres and not wybrany_okres.czy_zamrozony

        poczatek_roku = date(wybrany_okres.rok, 1, 1) if wybrany_okres else date.today()
        koniec_roku = date(wybrany_okres.rok, 12, 31) if wybrany_okres else date.today()

        return okresy_wszystkie, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku

    # Obsługa dodawania nowego podmiotu
    if request.method == 'POST' and 'add_grupanaglowek' in request.POST:
        form = GrupaNaglowekForm(request.POST)
        if form.is_valid():
            grupanaglowek_list = form.save(commit=False)
            grupanaglowek_list.utworzone_przez_uzytkownika = request.user.username
            grupanaglowek_list.save()
            return redirect(request.path_info)
    else:
        form = GrupaNaglowekForm()

    # Obsługa usuwania grupy
    if request.method == 'POST' and 'delete_grupanaglowek' in request.POST:
        grupanaglowek_id = request.POST.get('grupanaglowek_id')
        grupanaglowek = get_object_or_404(GrupaNaglowek, id=grupanaglowek_id)
        grupanaglowek.delete()
        return redirect(request.path_info)

    # Pobierz parametry filtrowania z żądania
    nazwa_filter = request.GET.get('nazwa', '')

    # Filtruj dane na podstawie parametrów
    grupanagloweks = GrupaNaglowek.objects.all()
    if nazwa_filter:
        grupanagloweks = grupanagloweks.filter(nazwa__icontains=nazwa_filter)

    # Pobierz liczbę wyników na stronę z żądania
    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(grupanagloweks, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'nazwa_filter': nazwa_filter,
        'results_per_page': results_per_page,
        'form': form,
    }

    return render(request, 'fossa2/grupanaglowek_list.html', context)


def grupa_podmioty_list(request):
    najnowszy_okres = OkresSprawozdawczy.objects.order_by('-rok').first()
    poczatek_roku = date(najnowszy_okres.rok, 1, 1) if najnowszy_okres else date.today().replace(month=1, day=1)

    grupa_filter = request.GET.get('grupa', '')
    podmiot_filter = request.GET.get('podmiot', '')
    results_per_page = int(request.GET.get('results_per_page', 25))

    # -------- LOGIKA FORMULARZA (DODAWANIE) --------
    if request.method == 'POST' and 'add_grupa_podmioty' in request.POST:
        form = GrupaPodmiotyForm(request.POST)

        form.fields['id_grupa'].queryset = GrupaNaglowek.objects.filter(
            data_do=INFINITY_DATE,
            data_od=poczatek_roku
        )

        if form.is_valid():
            selected_podmioty = request.POST.getlist('selected_podmioty')
            grupa = form.cleaned_data['id_grupa']

            for podmiot_id in selected_podmioty:
                if not GrupaPodmioty.objects.filter(id_grupa=grupa, id_podmiotu_id=podmiot_id).exists():
                    GrupaPodmioty.objects.create(
                        id_grupa=grupa,
                        id_podmiotu_id=podmiot_id,
                        utworzone_przez_uzytkownika=request.user.username
                    )
            return redirect('grupa_podmioty_list')
    else:
        form = GrupaPodmiotyForm()
        form.fields['id_grupa'].queryset = GrupaNaglowek.objects.filter(
            data_do=INFINITY_DATE,
            data_od=poczatek_roku
        )

    grupa_podmioty_qs = GrupaPodmioty.objects.filter(id_grupa__data_od=poczatek_roku)

    if grupa_filter:
        grupa_podmioty_qs = grupa_podmioty_qs.filter(id_grupa__nazwa__icontains=grupa_filter)
    if podmiot_filter:
        grupa_podmioty_qs = grupa_podmioty_qs.filter(id_podmiotu__nazwa__icontains=podmiot_filter)

    paginator = Paginator(grupa_podmioty_qs, results_per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    podmioty = Podmiot.objects.all()

    # -------- USUWANIE --------
    if request.method == 'POST' and 'delete_grupa_podmioty' in request.POST:
        grupa_podmioty_id = request.POST.get('grupa_podmioty_id')
        GrupaPodmioty.objects.filter(id=grupa_podmioty_id).delete()
        return redirect('grupa_podmioty_list')

    context = {
        'page_obj': page_obj,
        'podmiot_filter': podmiot_filter,
        'grupa_filter': grupa_filter,
        'results_per_page': results_per_page,
        'form': form,
        'podmioty': podmioty,
        'rok_opis': najnowszy_okres.rok if najnowszy_okres else ""
    }

    return render(request, 'fossa2/grupa_podmioty_list.html', context)


def ankieta_naglowek_list(request, ankieta_id=None):
    # Obsługa akcji dodawania
    if request.method == 'POST' and 'add_ankieta' in request.POST:
        form = AnkietaNaglowekForm(request.POST)
        if form.is_valid():
            ankieta_naglowek_list = form.save(commit=False)
            ankieta_naglowek_list.utworzone_przez_uzytkownika = request.user.username
            ankieta_naglowek_list.save()
            return redirect('ankieta_naglowek_list')

    # Obsługa akcji usuwania
    if request.method == 'POST' and 'delete_ankieta' in request.POST:
        ankieta = AnkietaNaglowek.objects.get(id=request.POST['ankieta_id'])
        ankieta.delete()
        return redirect('ankieta_naglowek_list')

    # Filtry
    nazwa_filter = request.GET.get('nazwa', '')
    grupa_filter = request.GET.get('grupa', '')

    # Pobranie rekordów z filtrem
    ankiety = AnkietaNaglowek.objects.all()

    if nazwa_filter:
        ankiety = ankiety.filter(nazwa__icontains=nazwa_filter)
    if grupa_filter:
        ankiety = ankiety.filter(id_grupa__id=grupa_filter)

    results_per_page = int(request.GET.get('results_per_page', 25))

    # Paginacja
    paginator = Paginator(ankiety, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Formularz dodawania
    form = AnkietaNaglowekForm()

    # Dla filtru grupy
    grupy = GrupaNaglowek.objects.all()

    context = {
        'page_obj': page_obj,
        'form': form,
        'grupy': grupy,
        'nazwa_filter': nazwa_filter,
        'grupa_filter': grupa_filter,
        'results_per_page': results_per_page,
    }

    return render(request, 'fossa2/ankieta_naglowek_list.html', context)



def ankieta_pytania_list(request):
    najnowszy_okres = OkresSprawozdawczy.objects.order_by('-rok').first()
    poczatek_roku = date(najnowszy_okres.rok, 1, 1) if najnowszy_okres else date.today().replace(month=1, day=1)
    # 1. Pobieranie parametrów filtrów i ustawień
    ankieta_filter = request.GET.get('ankieta', '')
    obszar_filter = request.GET.get('obszar', '')
    blok_filter = request.GET.get('blok', '')
    podblok_filter = request.GET.get('podblok', '')
    pytanie_filter = request.GET.get('pytanie', '')
    podzapytanie_filter = request.GET.get('podzapytanie', '')

    # Wyniki na stronę (RPP)
    rpp = request.GET.get('results_per_page', '25')
    try:
        results_per_page = int(rpp)
    except ValueError:
        results_per_page = 25

    def get_natural_sort_key(value):
        if not value:
            return []
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', str(value))]


    # Pobieramy bazowy QuerySet dla sekcji B
    ankieta_pytania_qs = AnkietaPytania.objects.select_related(
        'id_podzapytania__id_pytania__id_podbloku__id_bloku__id_obszaru',
        'id_ankieta_naglowek'
    ).filter(
        id_ankieta_naglowek__data_od=poczatek_roku,
        id_ankieta_naglowek__data_do=INFINITY_DATE,
        id_podzapytania__data_do=INFINITY_DATE
    )

    # Nakładanie filtrów na sekcję B
    if ankieta_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(id_ankieta_naglowek__nazwa__icontains=ankieta_filter)
    if obszar_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(
            id_podzapytania__id_pytania__id_podbloku__id_bloku__id_obszaru__kod__icontains=obszar_filter)
    if blok_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(
            id_podzapytania__id_pytania__id_podbloku__id_bloku__kod__icontains=blok_filter)
    if podblok_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(
            id_podzapytania__id_pytania__id_podbloku__kod__icontains=podblok_filter)
    if pytanie_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(id_podzapytania__id_pytania__tresc__icontains=pytanie_filter)
    if podzapytanie_filter:
        ankieta_pytania_qs = ankieta_pytania_qs.filter(id_podzapytania__tresc__icontains=podzapytanie_filter)

    # Konwersja na listę i sortowanie naturalne dla sekcji B
    ankieta_pytania_list = list(ankieta_pytania_qs)
    ankieta_pytania_list.sort(
        key=lambda obj: get_natural_sort_key(obj.id_podzapytania.kod if obj.id_podzapytania else ""))

    # Paginacja sekcji B
    paginator_list = Paginator(ankieta_pytania_list, results_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator_list.get_page(page_number)

    # =========================================================
    # SEKCJA A: BUDOWANIE ANKIETY (Dodawanie pytań)
    # =========================================================

    wszystkie_qs = Podzapytanie.objects.select_related(
        'id_pytania__id_podbloku__id_bloku__id_obszaru'
    ).filter(
        data_do=INFINITY_DATE
    )
    print(wszystkie_qs)
    if obszar_filter:
        wszystkie_qs = wszystkie_qs.filter(
            id_pytania__id_podbloku__id_bloku__id_obszaru__kod__icontains=obszar_filter)

    if blok_filter:
        wszystkie_qs = wszystkie_qs.filter(
            id_pytania__id_podbloku__id_bloku__kod__icontains=blok_filter)

    if podblok_filter:
        wszystkie_qs = wszystkie_qs.filter(
            id_pytania__id_podbloku__kod__icontains=podblok_filter)

    if pytanie_filter:
        wszystkie_qs = wszystkie_qs.filter(
            id_pytania__kod__icontains=pytanie_filter)

    if podzapytanie_filter:
        wszystkie_qs = wszystkie_qs.filter(
            kod__icontains=podzapytanie_filter)


    tresc_filter = request.GET.get('tresc', '')
    if tresc_filter:
        wszystkie_qs = wszystkie_qs.filter(
            tresc__icontains=tresc_filter)
    # Konwersja na listę i sortowanie naturalne dla sekcji A (bez zmian)
    wszystkie_podzapytania_list = list(wszystkie_qs)
    wszystkie_podzapytania_list.sort(key=lambda obj: get_natural_sort_key(obj.kod))

    # Paginacja sekcji A
    paginator_add = Paginator(wszystkie_podzapytania_list, results_per_page)
    page_add_number = request.GET.get('page_add')
    wszystkie_podzapytania = paginator_add.get_page(page_add_number)

    # =========================================================
    # OBSŁUGA POST (Dodawanie / Usuwanie)
    # =========================================================
    if request.method == 'POST':
        if 'add_ankieta_pytania' in request.POST:
            form = AnkietaPytaniaForm(request.POST)
            form.fields['id_ankieta_naglowek'].queryset = AnkietaNaglowek.objects.filter(
                data_do=INFINITY_DATE,
                data_od=poczatek_roku
            )
            wybrane_ids = request.POST.getlist('wybrane_podzapytania')
            if form.is_valid():
                ankieta_obj = form.cleaned_data['id_ankieta_naglowek']
                for pz_id in wybrane_ids:
                    AnkietaPytania.objects.get_or_create(
                        id_ankieta_naglowek=ankieta_obj,
                        id_podzapytania_id=pz_id,
                        defaults={'utworzone_przez_uzytkownika': request.user.username}
                    )
                return redirect('ankieta_pytania_list')

        elif 'delete_ankieta_pytania' in request.POST:
            ap_id = request.POST.get('ankietapytania_id')
            get_object_or_404(AnkietaPytania, id=ap_id).delete()
            return redirect('/ankieta-pytania/?mode=list')
    else:
        form = AnkietaPytaniaForm()
        form.fields['id_ankieta_naglowek'].queryset = AnkietaNaglowek.objects.filter(
            data_do=INFINITY_DATE,
            data_od=poczatek_roku
        )

    context = {
        # Sekcja B
        'page_obj': page_obj,
        'ankieta_filter': ankieta_filter,
        'obszar_filter': obszar_filter,
        'blok_filter': blok_filter,
        'podblok_filter': podblok_filter,
        'pytanie_filter': pytanie_filter,
        'podzapytanie_filter': podzapytanie_filter,

        # Sekcja A
        'wszystkie_podzapytania': wszystkie_podzapytania,
        'form': form,


        'results_per_page': results_per_page,
    }

    return render(request, 'fossa2/ankieta_pytania_list.html', context)

def generowanie_formularzy(request):
    najnowszy_okres = OkresSprawozdawczy.objects.order_by('-rok').first()
    poczatek_roku = date(najnowszy_okres.rok, 1, 1) if najnowszy_okres else date.today().replace(month=1, day=1)
    if request.method == 'POST' and 'generuj' in request.POST:
        grupanaglowek_id = request.POST.get('grupanaglowek_id')
        print_on_terminal(grupanaglowek_id)
        data = get_data_by_grupanaglowek_id(grupanaglowek_id)
        print(transform_dict(data))



    grupanagloweks = GrupaNaglowek.objects.filter(
        data_od=poczatek_roku,
        data_do=INFINITY_DATE
    )

    context = {
        'grupanagloweks': grupanagloweks,
    }
    return render(request, 'fossa2/generowanie_formularzy.html', context)

def print_on_terminal(grupanaglowek_id):
    print(f"Wywołano foo() z ID: {grupanaglowek_id}")