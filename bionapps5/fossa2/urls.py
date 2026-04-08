from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views, view
from .view.blok_views import BlokListView
from .view.podblok_views import PodblokListView

from .view.pytanie_views import PytanieListView
from .view.podzapytanie_views import  PodzapytanieListView
from .view.grupa_views import GrupaNaglowekListView
from .view.ankieta_views import AnkietaNaglowekListView
from .view.menu_views import HomeView
from .views import PodmiotViewSet
from .view.grupa_obszarow_views import GrupaObszarowListView
from .view.obszar_views import ObszarListView

router = DefaultRouter()
router.register(r'podmioty', PodmiotViewSet)
urlpatterns = [
    path('', HomeView.as_view(), name='strona_glowna'),
    path('api/', include(router.urls)),
    path('grupy_obszarow/', GrupaObszarowListView.as_view(), name='grupa_obszarow_list'),
    path('obszary/', ObszarListView.as_view(), name='obszar_list'),
    path('podmiot_list/', views.podmiot_list, name='podmiot_list'),
    path('bloki/', BlokListView.as_view(), name='blok_list'),
    path('podblok/', PodblokListView.as_view(), name='podblok_list'),
    path('ajax/load-bloki/', views.ajax_load_bloki, name='ajax_load_bloki'),
    path('ajax/load-podbloki/', views.ajax_load_podbloki, name='ajax_load_podbloki'),
    path('ajax/load-pytania/', views.ajax_load_pytania, name='ajax_load_pytania'),  # DODAJ TO

    path('pytania/', PytanieListView.as_view(), name='pytanie_list'),
    path('podzapytania/', PodzapytanieListView.as_view(), name='podzapytanie_list'),
    #path('grupy-naglowkow/', views.grupanaglowek_list, name='grupanaglowek_list'),
    path('grupy-naglowkow/', GrupaNaglowekListView.as_view(), name='grupanaglowek_list'),
    path('grupy-podmiotow/', views.grupa_podmioty_list, name='grupa_podmioty_list'),
    #path('ankieta-naglowek/', , name='ankieta_naglowek_list'),
    path('ankieta-naglowek/', AnkietaNaglowekListView.as_view(), name='ankieta_naglowek_list'),
    path('ankieta-pytania/', views.ankieta_pytania_list, name='ankieta_pytania_list'),
    path('generowanie-formularzy/', views.generowanie_formularzy, name='generowanie_formularzy'),
]