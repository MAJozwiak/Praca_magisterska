from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import date

from fossa2.forms import PytanieForm
from fossa2.models import Pytanie, OkresSprawozdawczy, INFINITY_DATE
from fossa2.models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie

class PytanieListView(View):
    template_name = 'fossa2/pytanie_list.html'

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

    def list_pytania(self, request, extra_context=None):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku = self.get_okres_context(request)

        obs_val = request.GET.get('id_obszaru', '')
        blok_val = request.GET.get('id_bloku', '')
        pod_val = request.GET.get('id_podbloku', '')
        kod_val = request.GET.get('kod', '')
        trs_val = request.GET.get('tresc', '')
        rpp = int(request.GET.get('results_per_page', 25))

        # Filtrowanie po dacie (pobieramy tylko aktywne w danym roku)
        if wybrany_okres:
            queryset = Pytanie.objects.filter(
                data_od__lte=koniec_roku,
                data_do__gte=poczatek_roku
            ).select_related('id_podbloku__id_bloku__id_obszaru')
        else:
            queryset = Pytanie.objects.none()

        # Filtry wyszukiwania
        if obs_val: queryset = queryset.filter(id_podbloku__id_bloku__id_obszaru__kod__icontains=obs_val)
        if blok_val: queryset = queryset.filter(id_podbloku__id_bloku__kod__icontains=blok_val)
        if pod_val: queryset = queryset.filter(id_podbloku__kod__icontains=pod_val)
        if kod_val: queryset = queryset.filter(kod__icontains=kod_val)
        if trs_val: queryset = queryset.filter(tresc__icontains=trs_val)

        paginator = Paginator(queryset, rpp)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'form': PytanieForm(),
            'id_obszaru_filter': obs_val,
            'id_bloku_filter': blok_val,
            'id_podbloku_filter': pod_val,
            'kod_filter': kod_val,
            'tresc_filter': trs_val,
            'results_per_page': rpp,
            'okresy_wszystkie': okresy,
            'wybrany_okres': wybrany_okres,
            'czy_tryb_edycji': czy_tryb_edycji,
        }
        return render(request, self.template_name, context)

    def generate_next_code(self, podblok_rodzic):
        prefix = podblok_rodzic.kod
        # Szukamy tylko wśród aktualnie aktywnych pytań, by uniknąć duplikacji kodów
        ostatnie = podblok_rodzic.pytania.filter(data_do=INFINITY_DATE)

        if ostatnie.exists():
            suffixes = []
            for p in ostatnie:
                try:
                    suffix = p.kod.split('.')[-1]
                    suffixes.append(int(suffix))
                except (ValueError, IndexError):
                    continue
            next_num = max(suffixes) + 1 if suffixes else 1
            return f"{prefix}.{next_num}"
        return f"{prefix}.1"

    def handle_add_pytanie(self, request, wybrany_okres):
        form = PytanieForm(request.POST)
        if form.is_valid():
            pytanie = form.save(commit=False)
            pytanie.kod = self.generate_next_code(pytanie.id_podbloku)
            pytanie.utworzone_przez_uzytkownika = request.user.username
            pytanie.data_od = date(wybrany_okres.rok, 1, 1)
            pytanie.data_do = INFINITY_DATE
            pytanie.save()
            return True, None
        return False, form

    def handle_delete_pytanie(self, request, wybrany_okres):
        pyt_id = request.POST.get('pytanie_id')
        if pyt_id:
            pytanie = get_object_or_404(Pytanie, id=pyt_id)
            if pytanie.czy_z_biezacego_roku(wybrany_okres.rok):
                pytanie.delete()
            else:
                pytanie.data_do = date(wybrany_okres.rok - 1, 12, 31)
                pytanie.save()
                data_zamkniecia = date(wybrany_okres.rok - 1, 12, 31)
                # 3. Zamykamy wszystkie AKTYWNE Pytania podpięte pod ten Podblok
                # Używamy .update(), bo to najszybsza metoda (jedno zapytanie SQL)

                # 4. Zamykamy wszystkie AKTYWNE Podzapytania podpięte pod te Pytania
                # Używamy podwójnego podkreślenia (__), aby sięgnąć głębiej w relację
                Podzapytanie.objects.filter(
                    id_pytania=pytanie,  # Używamy obiektu 'pytanie', który mamy pod ręką
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)

    def handle_edit_pytanie(self, request, wybrany_okres):
        pyt_id = request.POST.get('pytanie_id')
        nowa_tresc = request.POST.get('tresc')
        if pyt_id and nowa_tresc:
            pytanie = get_object_or_404(Pytanie, id=pyt_id)
            if pytanie.czy_z_biezacego_roku(wybrany_okres.rok):
                pytanie.tresc = nowa_tresc
                pytanie.save()
            else:
                pytanie.data_do = date(wybrany_okres.rok - 1, 12, 31)
                pytanie.save()
                pytanie_archiwalne=Pytanie.objects.create(
                    id_podbloku=pytanie.id_podbloku,
                    kod=pytanie.kod,
                    tresc=nowa_tresc,
                    utworzone_przez_uzytkownika=request.user.username,
                    data_od=date(wybrany_okres.rok, 1, 1),
                    data_do=INFINITY_DATE
                )
                koniec_zeszlego_roku = date(wybrany_okres.rok - 1, 12, 31)
                poczatek_tego_roku = date(wybrany_okres.rok, 1, 1)
                podzapytania = Podzapytanie.objects.filter(id_pytania=pytanie)
                for podzap in podzapytania:
                    Podzapytanie.objects.create(
                        id_pytania=pytanie_archiwalne,  # Przypisane do PYTANIA ARCHIWALNEGO
                        kod=podzap.kod,
                        tresc=podzap.tresc,
                        utworzone_przez_uzytkownika=podzap.utworzone_przez_uzytkownika,
                        data_od=podzap.data_od,
                        data_do=koniec_zeszlego_roku
                    )

                    podzap.data_od = poczatek_tego_roku
                    podzap.data_do = INFINITY_DATE
                    podzap.utworzone_przez_uzytkownika = request.user.username
                    podzap.save()

    def get(self, request, *args, **kwargs):
        return self.list_pytania(request)

    def post(self, request, *args, **kwargs):
        okresy, wybrany_okres, czy_tryb_edycji, _, _ = self.get_okres_context(request)
        success_url = request.META.get('HTTP_REFERER', request.path_info)

        if not czy_tryb_edycji:
            return HttpResponseForbidden("Okres jest zamrożony.")

        if 'add_pytanie' in request.POST:
            success, _ = self.handle_add_pytanie(request, wybrany_okres)
            if success: return redirect(success_url)

        if 'delete_pytanie' in request.POST:
            self.handle_delete_pytanie(request, wybrany_okres)
            return redirect(success_url)

        if 'edit_pytanie' in request.POST:
            self.handle_edit_pytanie(request, wybrany_okres)
            return redirect(success_url)

        return redirect(success_url)