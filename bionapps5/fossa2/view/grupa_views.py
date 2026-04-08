from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import date
from fossa2.models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie
from fossa2.forms import GrupaNaglowekForm
from fossa2.models import Blok, OkresSprawozdawczy, INFINITY_DATE


class GrupaNaglowekListView(View):
    template_name = 'fossa2/grupanaglowek_list.html'

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
        results_per_page = int(request.GET.get('results_per_page', 25))


        if not czy_tryb_edycji:
            GrupaNaglowek.objects.filter(
                data_od=poczatek,
                data_do=INFINITY_DATE
            ).update(data_do=koniec)

        # --- FILTROWANIE (Zapobieganie duplikatom) ---
        queryset = GrupaNaglowek.objects.filter(data_od=poczatek)

        if nazwa_filter:
            queryset = queryset.filter(nazwa__icontains=nazwa_filter)

        paginator = Paginator(queryset, results_per_page)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'nazwa_filter': nazwa_filter,
            'results_per_page': results_per_page,
            'form': GrupaNaglowekForm(),
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
        if 'add_grupanaglowek' in request.POST:
            form = GrupaNaglowekForm(request.POST)
            if form.is_valid():
                grupa = form.save(commit=False)
                grupa.utworzone_przez_uzytkownika = request.user.username
                grupa.data_od = poczatek
                grupa.data_do = INFINITY_DATE
                grupa.save()
            return redirect(success_url)

        # USUWANIE
        if 'delete_grupanaglowek' in request.POST:
            grupa_id = request.POST.get('grupanaglowek_id')
            grupa = get_object_or_404(GrupaNaglowek, id=grupa_id)
            # Skoro każda wersja roku ma swój rekord, usuwamy go fizycznie
            grupa.delete()
            return redirect(success_url)

        return redirect(success_url)