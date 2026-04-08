from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from fossa2.forms import PodblokForm
from datetime import date
from fossa2.models import Podblok, OkresSprawozdawczy, INFINITY_DATE
from fossa2.models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie

class PodblokListView(View):
    template_name = 'fossa2/podblok_list.html'

    def migruj_podbloki_dla_bloku(blok_id, rok_wybrany, username, INFINITY_DATE):
        """
        Funkcja archiwizuje stare podbloki i aktualizuje obecne na nowy rok.
        """

        koniec_zeszlego_roku = date(rok_wybrany - 1, 12, 31)
        poczatek_tego_roku = date(rok_wybrany, 1, 1)

        # Pobieramy wszystkie podbloki przypisane do tego bloku
        podbloki = Podblok.objects.filter(id_bloku=blok_id)

        for podblok in podbloki:
            # A. Tworzymy kopię archiwalną (nowy rekord, inne ID)
            Podblok.objects.create(
                id_bloku=podblok.id_bloku,
                kod=podblok.kod,
                tresc=podblok.tresc,
                utworzone_przez_uzytkownika=podblok.utworzone_przez_uzytkownika,
                data_od=podblok.data_od,
                data_do=koniec_zeszlego_roku
            )

            # B. Aktualizujemy istniejący rekord (ten sam ID zostaje dla relacji)
            podblok.data_od = poczatek_tego_roku
            podblok.data_do = INFINITY_DATE
            podblok.utworzone_przez_uzytkownika = username
            # Jeśli treść podbloku też ma się zmienić, musiałbyś ją przekazać,
            # ale zazwyczaj przy migracji struktury zmienia się tylko daty.
            podblok.save()

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

    # --- FUNKCJA POMOCNICZA: Ogarnianie wybranego roku sprawozdawczego ---
    def list_podbloki(self, request, extra_context=None):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku = self.get_okres_context(request)

        obs_val = request.GET.get('id_obszaru', '')
        blok_val = request.GET.get('id_bloku', '')
        kod_val = request.GET.get('kod', '')
        trs_val = request.GET.get('tresc', '')
        rpp_val = int(request.GET.get('results_per_page', 25))

        # ODKOMENTOWANE I NAPRAWIONE: Pobieramy poprawnie tylko Podbloki z wybranego roku!
        if wybrany_okres:
            queryset = Podblok.objects.filter(
                data_od__lte=koniec_roku,
                data_do__gte=poczatek_roku
            ).select_related('id_bloku__id_obszaru')
        else:
            queryset = Podblok.objects.none()  # BYŁO Blok.objects.none(), co powodowało błąd!

        # Filtrowanie "w górę" po relacjach
        if obs_val:
            queryset = queryset.filter(id_bloku__id_obszaru__kod__icontains=obs_val)
        if blok_val:
            queryset = queryset.filter(id_bloku__kod__icontains=blok_val)
        if kod_val:
            queryset = queryset.filter(kod__icontains=kod_val)
        if trs_val:
            queryset = queryset.filter(tresc__icontains=trs_val)

        # Paginacja
        paginator = Paginator(queryset, rpp_val)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'form': PodblokForm(),
            'id_obszaru_filter': obs_val,
            'id_bloku_filter': blok_val,
            'kod_filter': kod_val,
            'tresc_filter': trs_val,
            'results_per_page': rpp_val,
            'okresy_wszystkie': okresy,
            'wybrany_okres': wybrany_okres,
            'czy_tryb_edycji': czy_tryb_edycji,
        }

        if extra_context:
            context.update(extra_context)

        return render(request, self.template_name, context)

    # --- 2. GENEROWANIE KODU (Poprawione) ---
    def generate_next_code(self, blok_rodzic):
        prefix = blok_rodzic.kod  # np. "1"

        # POPRAWKA: Musimy brać pod uwagę tylko aktywne podbloki, inaczej kody zaczną wariować!
        ostatnie = blok_rodzic.podbloki.filter(data_do=INFINITY_DATE)

        if ostatnie.exists():
            kody_numeryczne = []
            for pb in ostatnie:
                try:
                    suffix = pb.kod.split('.')[-1]
                    kody_numeryczne.append(int(suffix))
                except (ValueError, IndexError):
                    continue

            nastepny_numer = max(kody_numeryczne) + 1 if kody_numeryczne else 1
            return f"{prefix}.{nastepny_numer}"

        return f"{prefix}.1"

    # --- 3. DODAWANIE (Poprawione) ---
    def handle_add_podblok(self, request, wybrany_okres):
        form = PodblokForm(request.POST)
        if form.is_valid():
            podblok = form.save(commit=False)
            podblok.kod = self.generate_next_code(podblok.id_bloku)
            podblok.utworzone_przez_uzytkownika = request.user.username
            podblok.data_od = date(wybrany_okres.rok, 1, 1)
            podblok.data_do = INFINITY_DATE
            podblok.save()
            return True, None

        # POPRAWKA: Wcześniej zwracałeś samo `return False`. Skoro w post masz `success, result = self.handle_add_podblok...`, to wyrzuciłoby błąd.
        return False, form

    def handle_delete_podblok(self, request, wybrany_okres):
        podblok_id = request.POST.get('podblok_id')
        if podblok_id:
            podblok = get_object_or_404(Podblok, id=podblok_id)

            if podblok.czy_z_biezacego_roku(wybrany_okres.rok): #kiedy record zostal usuniety w biezacym roku
                podblok.delete()
            else:
                podblok.data_do = date(wybrany_okres.rok - 1, 12, 31) #jesli record zostal utworzony w ubieglych latach
                podblok.save()
                data_zamkniecia = date(wybrany_okres.rok - 1, 12, 31)
                # 3. Zamykamy wszystkie AKTYWNE Pytania podpięte pod ten Podblok
                # Używamy .update(), bo to najszybsza metoda (jedno zapytanie SQL)
                Pytanie.objects.filter(
                    id_podbloku=podblok,
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)

                # 4. Zamykamy wszystkie AKTYWNE Podzapytania podpięte pod te Pytania
                # Używamy podwójnego podkreślenia (__), aby sięgnąć głębiej w relację
                Podzapytanie.objects.filter(
                    id_pytania__id_podbloku=podblok,
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)


    def handle_edit_podblok(self, request, wybrany_okres):
        podblok_id = request.POST.get('podblok_id')
        nowa_tresc = request.POST.get('tresc')

        if podblok_id and nowa_tresc:
            podblok = get_object_or_404(Podblok, id=podblok_id)

            if podblok.czy_z_biezacego_roku(wybrany_okres.rok):
                podblok.tresc = nowa_tresc
                podblok.save()
            else:
                podblok_archiwalny= Podblok.objects.create(
                    id_bloku=podblok.id_bloku,
                    kod=podblok.kod,
                    tresc=podblok.tresc,  # Stara treść trafia do archiwum
                    utworzone_przez_uzytkownika=podblok.utworzone_przez_uzytkownika,
                    data_od=podblok.data_od,
                    data_do=date(wybrany_okres.rok - 1, 12, 31)  # Zamykamy na koniec zeszłego roku
                )
                data_zamkniecia = date(wybrany_okres.rok - 1, 12, 31)




                podblok.tresc = nowa_tresc  # Nowa treść w starym ID
                podblok.data_od = date(wybrany_okres.rok, 1, 1)  # Startuje w tym roku
                podblok.data_do = INFINITY_DATE  # Jest otwarty
                podblok.utworzone_przez_uzytkownika = request.user.username
                podblok.save()
                koniec_zeszlego_roku = date(wybrany_okres.rok - 1, 12, 31)
                poczatek_tego_roku = date(wybrany_okres.rok, 1, 1)
                # 3. PYTANIA
                pytania = Pytanie.objects.filter(id_podbloku=podblok)
                for pytanie in pytania:
                    pytanie_archiwalne = Pytanie.objects.create(
                        id_podbloku=podblok_archiwalny,  # Przypisane do PODBLOKU ARCHIWALNEGO
                        kod=pytanie.kod,
                        tresc=pytanie.tresc,
                        utworzone_przez_uzytkownika=pytanie.utworzone_przez_uzytkownika,
                        data_od=pytanie.data_od,
                        data_do=koniec_zeszlego_roku
                    )

                    pytanie.data_od = poczatek_tego_roku
                    pytanie.data_do = INFINITY_DATE
                    pytanie.utworzone_przez_uzytkownika = request.user.username
                    pytanie.save()

                    # 4. PODZAPYTANIA
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
         return self.list_podbloki(request)

    def post(self, request, *args, **kwargs):
        okresy, wybrany_okres, czy_tryb_edycji, _, _ = self.get_okres_context(request)
        success_url = request.META.get('HTTP_REFERER', request.path_info)

        if not czy_tryb_edycji:
            return HttpResponseForbidden("Okres jest zamrożony. Brak uprawnień do edycji.")

        if 'add_podblok' in request.POST:
            success, result = self.handle_add_podblok(request, wybrany_okres)
            if success: return redirect(success_url)

        if 'delete_podblok' in request.POST:
            self.handle_delete_podblok(request, wybrany_okres)
            return redirect(success_url)

        if 'edit_podblok' in request.POST:
            self.handle_edit_podblok(request, wybrany_okres)
            return redirect(success_url)

        return redirect(success_url)