from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from fossa2.models import Obszar
from fossa2.forms import ObszarForm


class ObszarListView(View):
    template_name = 'fossa2/obszar_list.html'

    def get(self, request):
        # --- FILTROWANIE ---
        kod_filter = request.GET.get('kod', '')
        nazwa_filter = request.GET.get('nazwa', '')
        results_per_page = int(request.GET.get('results_per_page', 25))

        obszary = Obszar.objects.all()
        if kod_filter:
            obszary = obszary.filter(kod__icontains=kod_filter)
        if nazwa_filter:
            obszary = obszary.filter(nazwa__icontains=nazwa_filter)

        # --- PAGINACJA ---
        paginator = Paginator(obszary, results_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # --- FORMULARZ ---
        form = ObszarForm()

        context = {
            'page_obj': page_obj,
            'kod_filter': kod_filter,
            'nazwa_filter': nazwa_filter,
            'results_per_page': results_per_page,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        success_url = request.path_info  # zachowuje filtrację po przeładowaniu

        # --- DODAWANIE NOWEGO OBSZARU ---
        if 'add_obszar' in request.POST:
            form = ObszarForm(request.POST)
            if form.is_valid():
                obszar = form.save(commit=False)
                obszar.utworzone_przez_uzytkownika = request.user.username
                obszar.save()
            return redirect(success_url)

        # --- USUWANIE OBSZARU ---
        if 'delete_obszar' in request.POST:
            obszar_id = request.POST.get('obszar_id')
            obszar = get_object_or_404(Obszar, id=obszar_id)
            obszar.delete()
            return redirect(success_url)

        return redirect(success_url)
