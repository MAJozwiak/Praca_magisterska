from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import date
from fossa2.models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie
from fossa2.forms import AnkietaNaglowekForm
from fossa2.models import Blok, OkresSprawozdawczy, INFINITY_DATE


class AnkietaNaglowekListView(View):
    template_name = 'fossa2/ankieta_naglowek_list.html'

    def get_okres_context(self, request):
        okresy_wszystkie = OkresSprawozdawczy.objects.all()
        rok_param = request.GET.get('rok') or request.POST.get('rok')

        if rok_param:
            wybrany_okres = get_object_or_404(OkresSprawozdawczy, rok=int(rok_param))
        else:
            wybrany_okres = OkresSprawozdawczy.get_aktywny_rok() or okresy_wszystkie.first()

        czy_tryb_edycji = wybrany_okres and not wybrany_okres.czy_zamrozony
        poczatek_roku = date(wybrany_okres.rok, 1, 1)
        koniec_roku = date(wybrany_okres.rok, 12, 31)

        return okresy_wszystkie, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku

    def get(self, request):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek, koniec = self.get_okres_context(request)
        nazwa_filter = request.GET.get('nazwa', '')
        grupa_filter = request.GET.get('grupa', '')
        results_per_page = int(request.GET.get('results_per_page', 25))

        # --- LOGIKA AUTOMATYCZNEGO ZAMYKANIA ANKIET ---
        if not czy_tryb_edycji:
            AnkietaNaglowek.objects.filter(
                data_od=poczatek,
                data_do=INFINITY_DATE
            ).update(data_do=koniec)

        # 1. FILTROWANIE TABELI (Tylko ankiety z tego konkretnego roku)
        queryset = AnkietaNaglowek.objects.filter(data_od=poczatek)

        if nazwa_filter:
            queryset = queryset.filter(nazwa__icontains=nazwa_filter)
        if grupa_filter:
            queryset = queryset.filter(id_grupa__id=grupa_filter)

        # 2. PRZYGOTOWANIE FORMULARZA (Dodawanie)
        form = AnkietaNaglowekForm()
        if czy_tryb_edycji:
            form.fields['id_grupa'].queryset = GrupaNaglowek.objects.filter(
                data_od=poczatek,
                data_do=INFINITY_DATE
            )
        else:
            form.fields['id_grupa'].queryset = GrupaNaglowek.objects.none()

        grupy_do_filtra = GrupaNaglowek.objects.filter(data_od=poczatek)
        paginator = Paginator(queryset, results_per_page)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'form': form,
            'grupy': grupy_do_filtra,
            'nazwa_filter': nazwa_filter,
            'grupa_filter': grupa_filter,
            'results_per_page': results_per_page,
            'okresy_wszystkie': okresy,
            'wybrany_okres': wybrany_okres,
            'czy_tryb_edycji': czy_tryb_edycji,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek, koniec = self.get_okres_context(request)
        success_url = request.path_info + f"?rok={wybrany_okres.rok}"

        if not czy_tryb_edycji:
            return HttpResponseForbidden("Okres jest zamrożony.")

        # DODAWANIE
        if 'add_ankieta' in request.POST:
            form = AnkietaNaglowekForm(request.POST)
            # Walidacja: grupa musi być z tego roku i być otwarta
            form.fields['id_grupa'].queryset = GrupaNaglowek.objects.filter(
                data_od=poczatek,
                data_do=INFINITY_DATE
            )

            if form.is_valid():
                ankieta = form.save(commit=False)
                ankieta.utworzone_przez_uzytkownika = request.user.username
                ankieta.data_od = poczatek
                ankieta.data_do = INFINITY_DATE
                ankieta.save()
            return redirect(success_url)

        # USUWANIE
        if 'delete_ankieta' in request.POST:
            ankieta_id = request.POST.get('ankieta_id')
            ankieta = get_object_or_404(AnkietaNaglowek, id=ankieta_id)
            ankieta.delete()
            return redirect(success_url)

        return redirect(success_url)