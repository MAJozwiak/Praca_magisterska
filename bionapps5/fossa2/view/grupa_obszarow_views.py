from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from fossa2.models import GrupaObszarow
from fossa2.forms import GrupaObszarowForm


class GrupaObszarowListView(View):
    template_name = 'fossa2/grupa_obszarow_list.html'

    def get(self, request):
        # --- FILTROWANIE ---
        kod_filter = request.GET.get('kod', '')
        nazwa_filter = request.GET.get('nazwa', '')
        results_per_page = int(request.GET.get('results_per_page', 25))

        grupy = GrupaObszarow.objects.all()
        if kod_filter:
            grupy = grupy.filter(kod__icontains=kod_filter)
        if nazwa_filter:
            grupy = grupy.filter(nazwa__icontains=nazwa_filter)

        # --- PAGINACJA ---
        paginator = Paginator(grupy, results_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # --- FORMULARZ ---
        form = GrupaObszarowForm()

        context = {
            'page_obj': page_obj,
            'kod_filter': kod_filter,
            'nazwa_filter': nazwa_filter,
            'results_per_page': results_per_page,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        success_url = request.path_info

        # --- DODAWANIE ---
        if 'add_grupa' in request.POST:
            form = GrupaObszarowForm(request.POST)
            if form.is_valid():
                grupa = form.save(commit=False)
                grupa.utworzone_przez_uzytkownika = request.user.username
                grupa.save()
            return redirect(success_url)

        # --- USUWANIE ---
        if 'delete_grupa' in request.POST:
            grupa_id = request.POST.get('grupa_id')
            grupa = get_object_or_404(GrupaObszarow, id=grupa_id)
            grupa.delete()
            return redirect(success_url)

        return redirect(success_url)