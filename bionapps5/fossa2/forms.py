from django import forms
from .models import Podmiot, Obszar, Blok, Podblok, Pytanie, GrupaNaglowek, GrupaPodmioty, AnkietaNaglowek, \
    AnkietaPytania, Podzapytanie, GrupaObszarow


class PodmiotForm(forms.ModelForm):
    class Meta:
        model = Podmiot
        fields = ['kod', 'nazwa']
        widgets = {
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
        }

class GrupaObszarowForm(forms.ModelForm):
    class Meta:
        model = GrupaObszarow
        fields = ['kod', 'nazwa']
        widgets = {
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ObszarForm(forms.ModelForm):
    class Meta:
        model = Obszar
        fields = ['kod', 'nazwa']
        widgets = {
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BlokForm(forms.ModelForm):
    class Meta:
        model = Blok
        fields = ['id_obszaru', 'tresc']
        widgets = {
            'id_obszaru': forms.Select(attrs={'class': 'form-control'}),
            'tresc': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
class PustyBlokForm(BlokForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tresc'].required = False  # Tutaj na stałe wyłączamy wymaganie


class PodblokForm(forms.ModelForm):
    id_obszaru = forms.ModelChoiceField(
        queryset=Obszar.objects.all(),
        label="Obszar",
        widget=forms.Select(attrs={'id': 'id_obszaru_select', 'class': 'form-control'})
    )

    class Meta:
        model = Podblok
        fields = ['id_obszaru', 'id_bloku', 'tresc']
        widgets = {
            'id_bloku': forms.Select(attrs={'id': 'id_bloku_select', 'class': 'form-control'}),
            'tresc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formularz sam się "zeruje" przy każdym stworzeniu
        self.fields['id_bloku'].queryset = Blok.objects.none()

        # 2. TO JEST KLUCZ: Jeśli formularz został wysłany (jest w nim id_obszaru)
        # Musimy "podstawić" Django listę bloków z tego obszaru, żeby walidacja przeszła.
        if 'id_obszaru' in self.data:
            try:
                obszar_id = int(self.data.get('id_obszaru'))
                # Teraz Django wie, że bloki z tego obszaru są "legalne" do wyboru
                self.fields['id_bloku'].queryset = Blok.objects.filter(id_obszaru_id=obszar_id)
            except (ValueError, TypeError):
                pass  # Błędne ID, zostawiamy pusty queryset

        # 3. Dodatkowo: jeśli to jest edycja istniejącego podbloku
        if self.instance.pk and self.instance.id_bloku:
            self.fields['id_bloku'].queryset = self.instance.id_bloku.id_obszaru.bloki.all()

# class PustyPodblokForm(PodblokForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['tresc'].required = False  # Wyłączamy wymóg treści

class PytanieForm(forms.ModelForm):
    # Pole pomocnicze 1
    id_obszaru = forms.ModelChoiceField(
        queryset=Obszar.objects.all(),
        label="Obszar",
        widget=forms.Select(attrs={'id': 'id_obszaru_select', 'class': 'form-control'})
    )

    # Pole pomocnicze 2
    id_bloku = forms.ModelChoiceField(
        queryset=Blok.objects.all(),
        label="Blok",
        widget=forms.Select(attrs={'id': 'id_bloku_select', 'class': 'form-control'})
    )

    class Meta:
        model = Pytanie
        # id_podbloku to faktyczny rodzic pytania w bazie
        fields = ['id_obszaru', 'id_bloku', 'id_podbloku', 'tresc']
        widgets = {
            'id_podbloku': forms.Select(attrs={'id': 'id_podbloku_select', 'class': 'form-control'}),
            'tresc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. NA START: Blok i Podblok są puste
        self.fields['id_bloku'].queryset = Blok.objects.none()
        self.fields['id_podbloku'].queryset = Podblok.objects.none()

        # 2. WALIDACJA DLA POST (tak jak w podblokach):
        if 'id_obszaru' in self.data:
            try:
                area_id = int(self.data.get('id_obszaru'))
                self.fields['id_bloku'].queryset = Blok.objects.filter(id_obszaru_id=area_id)
            except (ValueError, TypeError):
                pass

        if 'id_bloku' in self.data:
            try:
                block_id = int(self.data.get('id_bloku'))
                self.fields['id_podbloku'].queryset = Podblok.objects.filter(id_bloku_id=block_id)
            except (ValueError, TypeError):
                pass


class PodzapytanieForm(forms.ModelForm):
    # Pole pomocnicze 1 (Pradziadek)
    id_obszaru = forms.ModelChoiceField(
        queryset=Obszar.objects.all(),
        label="Obszar",
        required=False,
        widget=forms.Select(attrs={'id': 'id_obszaru_select', 'class': 'form-control'})
    )

    # Pole pomocnicze 2 (Dziadek)
    id_bloku = forms.ModelChoiceField(
        queryset=Blok.objects.none(),
        label="Blok",
        required=False,
        widget=forms.Select(attrs={'id': 'id_bloku_select', 'class': 'form-control'})
    )

    # Pole pomocnicze 3 (Ojciec)
    id_podbloku = forms.ModelChoiceField(
        queryset=Podblok.objects.none(),
        label="Podblok",
        required=False,
        widget=forms.Select(attrs={'id': 'id_podbloku_select', 'class': 'form-control'})
    )

    class Meta:
        model = Podzapytanie  # Zakładam, że tak nazywa się Twój model
        # id_pytania to faktyczny rodzic podzapytania w bazie danych
        fields = ['id_obszaru', 'id_bloku', 'id_podbloku', 'id_pytania', 'tresc', 'obligatoryjne', 'wytyczne']
        widgets = {
            'id_pytania': forms.Select(attrs={'id': 'id_pytania_select', 'class': 'form-control'}),
            'tresc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style': 'resize: none;'}),
            'obligatoryjne': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'wytyczne': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. NA START: Wszystkie zależne pola są puste
        self.fields['id_bloku'].queryset = Blok.objects.none()
        self.fields['id_podbloku'].queryset = Podblok.objects.none()
        self.fields['id_pytania'].queryset = Pytanie.objects.none()

        # 2. DYNAMICZNA FILTRACJA DLA DANYCH POST (Walidacja formularza)
        data = self.data

        # Filtracja Bloków na podstawie Obszaru
        if 'id_obszaru' in data:
            try:
                area_id = int(data.get('id_obszaru'))
                self.fields['id_bloku'].queryset = Blok.objects.filter(id_obszaru_id=area_id)
            except (ValueError, TypeError):
                pass

        # Filtracja Podbloków na podstawie Bloku
        if 'id_bloku' in data:
            try:
                block_id = int(data.get('id_bloku'))
                self.fields['id_podbloku'].queryset = Podblok.objects.filter(id_bloku_id=block_id)
            except (ValueError, TypeError):
                pass

        # Filtracja Pytań na podstawie Podbloku
        if 'id_podbloku' in data:
            try:
                podblock_id = int(data.get('id_podbloku'))
                self.fields['id_pytania'].queryset = Pytanie.objects.filter(id_podbloku_id=podblock_id)
            except (ValueError, TypeError):
                pass

class GrupaNaglowekForm(forms.ModelForm):
    class Meta:
        model = GrupaNaglowek
        fields = ['nazwa']
        widgets = {
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
        }

class GrupaPodmiotyForm(forms.ModelForm):
    class Meta:
        model = GrupaPodmioty
        fields = ['id_grupa']
        widgets = {
            'id_grupa': forms.Select(attrs={'class': 'form-control'}),
        }


class AnkietaNaglowekForm(forms.ModelForm):
    class Meta:
        model = AnkietaNaglowek
        fields = ['nazwa', 'id_grupa']
        widgets = {
            'nazwa': forms.TextInput(attrs={'class': 'form-control'}),
            'id_grupa': forms.Select(attrs={'class': 'form-control'}),
        }


class AnkietaPytaniaForm(forms.ModelForm):
    class Meta:
        model = AnkietaPytania
        # USUNELIŚMY id_podzapytania stąd:
        fields = ['id_ankieta_naglowek']
        widgets = {
            'id_ankieta_naglowek': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        }