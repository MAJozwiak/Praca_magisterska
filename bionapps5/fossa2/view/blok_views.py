from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from datetime import date
from fossa2.models import Podmiot, Obszar, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podzapytanie
from fossa2.forms import BlokForm
from fossa2.models import Blok, OkresSprawozdawczy, INFINITY_DATE

class BlokListView(View):
    template_name = 'fossa2/blok_list.html'

    # --- FUNKCJA POMOCNICZA: Ogarnianie wybranego roku sprawozdawczego ---
    def get_okres_context(self, request):
        okresy_wszystkie = OkresSprawozdawczy.objects.all()

        # Pobieramy rok z filtra (GET) lub z przesłanego formularza (POST)
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


    def list_bloki(self, request, extra_context=None):
        okresy, wybrany_okres, czy_tryb_edycji, poczatek_roku, koniec_roku = self.get_okres_context(request)

        id_obszaru_ = request.GET.get('id_obszaru', '')
        kod = request.GET.get('kod', '')
        tresc = request.GET.get('tresc', '')
        results_per_page = int(request.GET.get('results_per_page', 25))


        if wybrany_okres:
            queryset = Blok.objects.filter(
                data_od__lte=koniec_roku,
                data_do__gte=poczatek_roku
            )

            obecne_kody = list(queryset.values_list('kod', flat=True))


            stare_bloki = Blok.objects.filter(data_do__lt=poczatek_roku) \
                .exclude(kod__in=obecne_kody) \
                .order_by('kod', '-data_do')
            usuniete_bloki = []
            widziane_kody = set()
            for b in stare_bloki:
                print(b.kod)
                if b.kod not in widziane_kody:
                    usuniete_bloki.append(b)
                    widziane_kody.add(b.kod)
        else:
            queryset = Blok.objects.none()


        # Filtry
        if id_obszaru_:
            queryset = queryset.filter(id_obszaru__kod__icontains=id_obszaru_)
        if kod:
            queryset = queryset.filter(kod__icontains=kod)
        if tresc:
            queryset = queryset.filter(tresc__icontains=tresc)

        paginator = Paginator(queryset, results_per_page)
        page_obj = paginator.get_page(request.GET.get('page'))

        context = {
            'page_obj': page_obj,
            'form': BlokForm(),
            'id_obszaru_filter': id_obszaru_,
            'kod_filter': kod,
            'tresc_filter': tresc,
            'results_per_page': results_per_page,

            'okresy_wszystkie': okresy,
            'wybrany_okres': wybrany_okres,
            'czy_tryb_edycji': czy_tryb_edycji,
            'usuniete_bloki': usuniete_bloki,
        }
        return render(request, self.template_name, context)

    def generate_next_code(self, obszar):
        ostatnie = obszar.bloki.filter(data_do=INFINITY_DATE)
        if ostatnie.exists():
            kody = [int(b.kod) for b in ostatnie if b.kod.isdigit()]
            return str(max(kody) + 1) if kody else "1"
        return "1"

    def handle_add_blok(self, request, wybrany_okres):
        form = BlokForm(request.POST)
        if form.is_valid():
            blok = form.save(commit=False)
            blok.kod = self.generate_next_code(blok.id_obszaru)
            blok.utworzone_przez_uzytkownika = request.user.username

            # Ustawiamy datę_od na 1 stycznia bieżącego roku sprawozdawczego
            blok.data_od = date(wybrany_okres.rok, 1, 1)
            blok.data_do = INFINITY_DATE
            blok.save()
            return True, None
        return False, form

    def handle_delete_blok(self, request, wybrany_okres):
        blok_id = request.POST.get('blok_id')
        if blok_id:
            blok = get_object_or_404(Blok, id=blok_id)
            # --- DEBUGOWANIE ---
            podbloki = blok.podbloki.all()  # Używamy related_name z modelu
            print(f"\n--- PRÓBA USUNIĘCIA BLOKU (ID: {blok.id}, Kod: {blok.kod}) ---")
            print(f"Liczba podpiętych podbloków: {podbloki.count()}")

            for pb in podbloki:
                print(f"  -> Znaleziono Podblok: ID: {pb.id}, Kod: {pb.kod}, Data_od: {pb.data_od}")
                # Sprawdźmy jeszcze głębiej - pytania pod tym podblokiem
                pytania_count = pb.pytania.count()
                if pytania_count > 0:
                    print(f"     [!] Ten podblok ma {pytania_count} pytań.")
            # -------------------
            if blok.czy_z_biezacego_roku(wybrany_okres.rok): #kiedy record zostal usuniety w biezacym roku
                blok.delete()
                print("delete")
            else:
                data_zamkniecia= date(wybrany_okres.rok - 1, 12, 31)
                blok.data_do = date(wybrany_okres.rok - 1, 12, 31) #jesli record zostal utworzony w ubieglych latach
                blok.save()
                Podblok.objects.filter(
                    id_bloku=blok,
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)

                # 3. Zamykamy wszystkie AKTYWNE Pytania (przez relację do bloku)
                Pytanie.objects.filter(
                    id_podbloku__id_bloku=blok,
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)

                # 4. Zamykamy wszystkie AKTYWNE Podzapytania (przez głęboką relację)
                Podzapytanie.objects.filter(
                    id_pytania__id_podbloku__id_bloku=blok,
                    data_do=INFINITY_DATE
                ).update(data_do=data_zamkniecia)



    def handle_edit_blok(self, request, wybrany_okres):
        blok_id = request.POST.get('blok_id')
        nowa_tresc = request.POST.get('tresc')

        if blok_id and nowa_tresc:
            blok = get_object_or_404(Blok, id=blok_id)

            if blok.czy_z_biezacego_roku(wybrany_okres.rok):
                blok.tresc = nowa_tresc
                blok.save()
            else:
                koniec_zeszlego_roku = date(wybrany_okres.rok - 1, 12, 31)
                poczatek_tego_roku = date(wybrany_okres.rok, 1, 1)

                # 1. TWORZYMY ARCHIWALNY BLOK I ZAPISUJEMY GO DO ZMIENNEJ
                blok_archiwalny = Blok.objects.create(
                    id_obszaru=blok.id_obszaru,
                    kod=blok.kod,
                    tresc=blok.tresc,
                    utworzone_przez_uzytkownika=blok.utworzone_przez_uzytkownika,
                    data_od=blok.data_od,
                    data_do=koniec_zeszlego_roku
                )
                blok.tresc = nowa_tresc
                blok.data_od = poczatek_tego_roku
                blok.data_do = INFINITY_DATE
                blok.utworzone_przez_uzytkownika = request.user.username
                blok.save()

                # 2. PODBLOKI
                podbloki = Podblok.objects.filter(id_bloku=blok)
                for podblok in podbloki:
                    podblok_archiwalny = Podblok.objects.create(
                        id_bloku=blok_archiwalny,  # Przypisany do BLOKU ARCHIWALNEGO
                        kod=podblok.kod,
                        tresc=podblok.tresc,
                        utworzone_przez_uzytkownika=podblok.utworzone_przez_uzytkownika,
                        data_od=podblok.data_od,
                        data_do=koniec_zeszlego_roku
                    )

                    podblok.data_od = poczatek_tego_roku
                    podblok.data_do = INFINITY_DATE
                    podblok.utworzone_przez_uzytkownika = request.user.username
                    podblok.save()

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
        return self.list_bloki(request)

    def post(self, request, *args, **kwargs):
        okresy, wybrany_okres, czy_tryb_edycji, _, _ = self.get_okres_context(request)
        success_url = request.META.get('HTTP_REFERER', request.path_info)

        if not czy_tryb_edycji:
            return HttpResponseForbidden("Okres jest zamrożony. Brak uprawnień do edycji.")

        if 'add_blok' in request.POST:
            success, result = self.handle_add_blok(request, wybrany_okres)
            if success: return redirect(success_url)

        if 'delete_blok' in request.POST:
            self.handle_delete_blok(request, wybrany_okres)
            return redirect(success_url)

        if 'edit_blok' in request.POST:
            self.handle_edit_blok(request, wybrany_okres)
            return redirect(success_url)


        return redirect(success_url)