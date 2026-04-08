from django.contrib import admin
from .models import Podmiot, Obszar, Pytanie, OkresSprawozdawczy, Blok, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, AnkietaPytania, \
    Podblok


@admin.register(Podmiot)
class PostPodmiot(admin.ModelAdmin):
    list_display = ['kod', 'nazwa', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    list_filter = ['kod', 'nazwa']
    search_fields = ['kod', 'nazwa']
    ordering = ['kod', 'nazwa']
    show_facets = admin.ShowFacets.ALWAYS


@admin.register(Obszar)
class PostObszar(admin.ModelAdmin):
    list_display = ['kod', 'nazwa', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    list_filter = ['kod']
    search_fields = ['kod', 'nazwa']
    ordering = ['kod', 'nazwa']
    show_facets = admin.ShowFacets.ALWAYS

@admin.register(OkresSprawozdawczy)
class PostOkresSprawozdawczyAdmin(admin.ModelAdmin):
    list_display = ('rok', 'czy_zamrozony')
    list_editable = ('czy_zamrozony',)
    ordering = ('-rok',)

@admin.register(Blok)
class PostBlok(admin.ModelAdmin):
    list_display = ['kod', 'id_obszaru', 'tresc', 'data_od', 'data_do', 'czy_aktywny_status']
    list_filter = ['id_obszaru', 'data_od', 'data_do']
    search_fields = ['kod', 'tresc']
    ordering =  ['kod', 'tresc']
    show_facets = admin.ShowFacets.ALWAYS

    def czy_aktywny_status(self, obj):
        return obj.czy_aktywny

    czy_aktywny_status.boolean = True
    czy_aktywny_status.short_description = "Aktywny?"

@admin.register(Podblok)
class PostPodblok(admin.ModelAdmin):
    list_display = ['kod', 'id_bloku', 'tresc',]
    list_filter = ['id_bloku__id_obszaru', 'id_bloku']
    search_fields = ['kod', 'tresc']

@admin.register(Pytanie)
class PostPytanie(admin.ModelAdmin):
    list_display = ['kod', 'id_podbloku', 'tresc']
    list_filter = ['id_podbloku__id_bloku__id_obszaru', 'id_podbloku__id_bloku']
    search_fields = [
        'kod',  # Szukaj po kodzie pytania (np. 1.1.1.1)
        'tresc',  # Szukaj po treści pytania
        'id_podbloku__kod',  # Szukaj po kodzie Podbloku (ojciec)
        'id_podbloku__id_bloku__kod'  # Szukaj po kodzie Bloku (dziadek)
    ]


@admin.register(GrupaNaglowek)
class PostGrupaNaglowek(admin.ModelAdmin):
    list_display = ['nazwa', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    ordering = ['nazwa']
    show_facets = admin.ShowFacets.ALWAYS

@admin.register(GrupaPodmioty)
class PostGrupaPodmioty(admin.ModelAdmin):
    list_display = ['id_podmiotu', 'id_grupa', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    show_facets = admin.ShowFacets.ALWAYS

@admin.register(AnkietaNaglowek)
class PostAnkietaNaglowek(admin.ModelAdmin):
    list_display = ['nazwa', 'id_grupa', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    show_facets = admin.ShowFacets.ALWAYS

@admin.register(AnkietaPytania)
class PostAnkietaPytania(admin.ModelAdmin):
    list_display = ['id_ankieta_naglowek', 'id_podzapytania', 'data_utworzenia', 'utworzone_przez_uzytkownika']
    show_facets = admin.ShowFacets.ALWAYS