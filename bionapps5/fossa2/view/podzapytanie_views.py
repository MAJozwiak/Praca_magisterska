from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import date

from fossa2.forms import PodzapytanieForm
from fossa2.models import Podzapytanie, OkresSprawozdawczy, INFINITY_DATE

class PodzapytanieListView(View):
    template_name = 'fossa2/podzapytanie_list.html'

    def get_okres_context(self, request):
        okresy_wszystkie = OkresSprawozdawczy.objects.all()
        rok_param = request.GET.get('rok') or request.POST.get('rok')

        if rok_param:
            wybrany_okres = get_object_or_404(OkresSprawozdawczy, rok=int(rok_param))
        else:
            wybrany_okres = OkresSprawozdawczy.get_aktywny_rok()
            if not wybrany_okres:
                wybrany_okres = okresy_wszystkie.first()

        czy_tryb_edycji = wybrany_okres and not wybrany_okres.czy_zamrozony

        if wybrany_okres:
            poczatek_roku = date(wybrany_okres.rok, 1, 1)
            koniec_roku = date(wybrany_okres.rok, 12, 31)
        else:
            poczatek_roku, koniec_roku = date.today(), date.today()

        return okresy_wszystkie, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku

    def list_podzapytanie(self, request):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku = self.get_okres_context(request)

        # Pobieranie filtrów
        obs_val = request.GET.get('id_obszaru', '')
        blok_val = request.GET.get('id_bloku', '')
        pod_val = request.GET.get('id_podbloku', '')
        pyt_val = request.GET.get('id_pytania', '')
        kod_val = request.GET.get('kod', '')
        trs_val = request.GET.get('tresc', '')
        rpp = int(request.GET.get('results_per_page', 25))

        if wybrany_okres:
            queryset = Podzapytanie.objects.filter(
                data_od__lte=koniec_roku,
                data_do__gte=poczatek_roku
            ).select_related('id_pytania__id_podbloku__id_bloku__id_obszaru')
        else:
            queryset = Podzapytanie.objects.none()

        # Filtrowanie
        if obs_val: queryset = queryset.filter(id_pytania__id_podbloku__id_bloku__id_obszaru__kod__icontains=obs_val)
        if blok_val: queryset = queryset.filter(id_pytania__id_podbloku__id_bloku__kod__icontains=blok_val)
        if pod_val: queryset = queryset.filter(id_pytania__id_podbloku__kod__icontains=pod_val)
        if pyt_val: queryset = queryset.filter(id_pytania__kod__icontains=pyt_val)
        if kod_val: queryset = queryset.filter(kod__icontains=kod_val)
        if trs_val: queryset = queryset.filter(tresc__icontains=trs_val)

        paginator = Paginator(queryset, rpp)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'form': PodzapytanieForm(),
            'id_obszaru_filter': obs_val,
            'id_bloku_filter': blok_val,
            'id_podbloku_filter': pod_val,
            'id_pytania_filter': pyt_val,
            'kod_filter': kod_val,
            'tresc_filter': trs_val,
            'results_per_page': rpp,
            'okresy_wszystkie': okresy,
            'wybrany_okres': wybrany_okres,
            'czy_tryb_edycji': czy_tryb_edycji,
        }
        return render(request, self.template_name, context)

    def generate_next_code(self, pytanie_rodzic):
        prefix = pytanie_rodzic.kod
        ostatnie = pytanie_rodzic.podzapytania.filter(data_do=INFINITY_DATE)
        if ostatnie.exists():
            suffixes = []
            for pz in ostatnie:
                try:
                    suffix = pz.kod.split('.')[-1]
                    suffixes.append(int(suffix))
                except (ValueError, IndexError):
                    continue
            next_num = max(suffixes) + 1 if suffixes else 1
            return f"{prefix}.{next_num}"
        return f"{prefix}.1"

    def handle_add_podzapytanie(self, request, wybrany_okres):
        form = PodzapytanieForm(request.POST)
        if form.is_valid():
            pz = form.save(commit=False)
            pz.kod = self.generate_next_code(pz.id_pytania)
            pz.utworzone_przez_uzytkownika = request.user.username
            pz.data_od = date(wybrany_okres.rok, 1, 1)
            pz.data_do = INFINITY_DATE
            pz.save()
            return True, None
        return False, form

    def handle_delete_podzapytanie(self, request, wybrany_okres):
        pz_id = request.POST.get('podzapytanie_id')
        if pz_id:
            pz = get_object_or_404(Podzapytanie, id=pz_id)
            if pz.czy_z_biezacego_roku(wybrany_okres.rok):
                pz.delete()
            else:
                pz.data_do = date(wybrany_okres.rok - 1, 12, 31)
                pz.save()

    def handle_edit_podzapytanie(self, request, wybrany_okres):
        pz_id = request.POST.get('podzapytanie_id')
        nowa_tresc = request.POST.get('tresc')
        nowe_wytyczne = request.POST.get('wytyczne')
        # Checkbox w HTML przesyła 'on' jeśli zaznaczony
        czy_obligatoryjne = request.POST.get('obligatoryjne') == 'on'

        if pz_id:
            pz = get_object_or_404(Podzapytanie, id=pz_id)
            if pz.czy_z_biezacego_roku(wybrany_okres.rok):
                pz.tresc = nowa_tresc
                pz.wytyczne = nowe_wytyczne
                pz.obligatoryjne = czy_obligatoryjne
                pz.save()
            else:
                koniec_zeszlego_roku = date(wybrany_okres.rok - 1, 12, 31)
                poczatek_tego_roku = date(wybrany_okres.rok, 1, 1)

                # 1. Tworzymy KOPIĘ ARCHIWALNĄ (dostanie nowe ID)
                # Przenosimy tam STARY tekst, aby historia była zachowana
                Podzapytanie.objects.create(
                    id_pytania=pz.id_pytania,
                    kod=pz.kod,
                    tresc=pz.tresc,  # STARY TEKST
                    wytyczne=pz.wytyczne,  # STARE WYTYCZNE
                    obligatoryjne=pz.obligatoryjne,
                    utworzone_przez_uzytkownika=pz.utworzone_przez_uzytkownika,
                    data_od=pz.data_od,
                    data_do=koniec_zeszlego_roku
                )

                # 2. AKTUALIZUJEMY ORYGINALNY REKORD (ten sam ID!)
                # Ten rekord jest już przypięty do tabeli AnkietaPytania
                pz.tresc = nowa_tresc  # NOWY TEKST
                pz.wytyczne = nowe_wytyczne  # NOWE WYTYCZNE
                pz.obligatoryjne = czy_obligatoryjne
                pz.data_od = poczatek_tego_roku
                pz.data_do = INFINITY_DATE
                pz.utworzone_przez_uzytkownika = request.user.username
                pz.save()


    def get(self, request, *args, **kwargs):
        return self.list_podzapytanie(request)

    def post(self, request, *args, **kwargs):
        _, wybrany_okres, czy_tryb_edycji, _, _ = self.get_okres_context(request)
        success_url = request.META.get('HTTP_REFERER', request.path_info)

        if not czy_tryb_edycji:
            return HttpResponseForbidden("Okres jest zamrożony.")

        if 'add_podzapytanie' in request.POST:
            self.handle_add_podzapytanie(request, wybrany_okres)
        elif 'delete_podzapytanie' in request.POST:
            self.handle_delete_podzapytanie(request, wybrany_okres)
        elif 'edit_podzapytanie' in request.POST:
            self.handle_edit_podzapytanie(request, wybrany_okres)

        return redirect(success_url)