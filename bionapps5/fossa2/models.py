from django.db import models
from datetime import date

class Podmiot(models.Model):
    kod = models.CharField(max_length=10, unique=True)
    nazwa = models.CharField(max_length=300)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.kod}"

    class Meta:
        ordering = ["kod"]

class GrupaObszarow(models.Model):
    kod = models.CharField(max_length=10, unique=True)
    nazwa = models.CharField(max_length=100, unique=True)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.kod}"

    class Meta:
        ordering = ["kod"]

class Obszar(models.Model):
    kod = models.CharField(max_length=10, unique=True)
    nazwa = models.CharField(max_length=100, unique=True)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.kod}"

    class Meta:
        ordering = ["kod"]



INFINITY_DATE = date(9999, 12, 31)
class OkresSprawozdawczy(models.Model):
    rok = models.IntegerField(unique=True, verbose_name="Rok sprawozdawczy")
    czy_zamrozony = models.BooleanField(default=False, verbose_name="Czy opublikowany/zamrożony?")

    class Meta:
        ordering = ['-rok']

    def __str__(self):
        status = "Zamrożony" if self.czy_zamrozony else "Otwarty"
        return f"{self.rok} ({status})"

    @classmethod
    def get_aktywny_rok(cls):
        return cls.objects.filter(czy_zamrozony=False).first()

    def zamroz_i_utworz_kolejny(self):
        self.czy_zamrozony = True
        self.save()

        nowy_rok = OkresSprawozdawczy.objects.create(
            rok=self.rok + 1,
            czy_zamrozony=False
        )
        return nowy_rok

class Blok(models.Model):
    id_obszaru = models.ForeignKey('Obszar', on_delete=models.CASCADE, related_name='bloki')
    kod = models.CharField(max_length=20, unique=False)
    tresc = models.CharField(max_length=300)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField(default=date.today)
    data_do = models.DateField(default=INFINITY_DATE)
    data_utworzenia = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kod} - {self.tresc[:30]}"

    class Meta:
        ordering = ["kod", "-data_od"]

    @property
    def czy_aktywny(self):
        return self.data_do == INFINITY_DATE

    def czy_z_biezacego_roku(self, rok_sprawozdawczy):
        return self.data_od.year == rok_sprawozdawczy


class Podblok(models.Model):
    id_bloku = models.ForeignKey(Blok, on_delete=models.CASCADE, related_name='podbloki')
    kod = models.CharField(max_length=20, unique=False)
    tresc = models.CharField(max_length=300)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField(default=date.today)
    data_do = models.DateField(default=INFINITY_DATE)
    data_utworzenia = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.kod}"

    class Meta:
        ordering = ["kod"]

    @property
    def czy_aktywny(self):
        return self.data_do == INFINITY_DATE

    def czy_z_biezacego_roku(self, rok_sprawozdawczy):
        return self.data_od.year == rok_sprawozdawczy


class Pytanie(models.Model):
    id_podbloku = models.ForeignKey(Podblok, on_delete=models.CASCADE, related_name='pytania')
    kod = models.CharField(max_length=20, unique=False)
    tresc = models.CharField(max_length=700)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField()
    data_do = models.DateField()

    def __str__(self):
        return f"{self.kod} - {self.tresc[:50]}"

    # DODAJ TĘ METODĘ (używamy jej w widoku do sprawdzania czy edytujemy bieżący rok):
    def czy_z_biezacego_roku(self, rok):
        return self.data_od.year == rok

class Podzapytanie(models.Model):
    id_pytania = models.ForeignKey(Pytanie, on_delete=models.CASCADE, related_name='podzapytania')
    kod = models.CharField(max_length=20, unique=False)
    tresc = models.CharField(max_length=700)
    obligatoryjne = models.BooleanField(default=True)
    wytyczne = models.CharField(max_length=700)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField()
    data_do = models.DateField()

    def __str__(self):
        return self.kod

    class Meta:
        ordering = ["kod"]

    def czy_z_biezacego_roku(self, rok):
        return self.data_od.year == rok

    def is_valid(self):
        pass


# Model GrupaNaglowek
#   Model zaprojektowany aby określać ogólne właściwości dla grupy
#
class GrupaNaglowek(models.Model):
    nazwa = models.CharField(max_length=10)
    data_utworzenia = models.DateField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField(default=date.today)
    data_do = models.DateField(default=INFINITY_DATE)

    def __str__(self):
        return self.nazwa

    class Meta:
        ordering = ["nazwa"]

# Model GrupaPodmioty
#   Model zaprojektowany, aby trzymać informację o podmiotach podpiętych do grupy
#   na potrzeby generowania arkuszy jakościowych
class GrupaPodmioty(models.Model):
    id_grupa = models.ForeignKey(GrupaNaglowek, on_delete=models.CASCADE)
    id_podmiotu = models.ForeignKey(Podmiot, on_delete=models.CASCADE, related_name='grupy_podmioty')
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField(default=date.today)
    data_do = models.DateField(default=INFINITY_DATE)

    def __str__(self):
        return f"{self.id_podmiotu}"

    class Meta:
        ordering = ["id_podmiotu"]


class AnkietaNaglowek(models.Model):
    nazwa = models.CharField(max_length=100)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    id_grupa = models.ForeignKey(GrupaNaglowek, on_delete=models.CASCADE)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)
    data_od = models.DateField(default=date.today)
    data_do = models.DateField(default=INFINITY_DATE)

    def __str__(self):
        return self.nazwa

    class Meta:
        ordering = ["nazwa"]


class AnkietaPytania(models.Model):
    id_ankieta_naglowek = models.ForeignKey(AnkietaNaglowek, on_delete=models.CASCADE)
    id_podzapytania = models.ForeignKey(Podzapytanie, on_delete=models.CASCADE)
    data_utworzenia = models.DateTimeField(auto_now_add=True)
    utworzone_przez_uzytkownika = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.id_ankieta_naglowek} - {self.id_podzapytania}"

    class Meta:
        ordering = ["id_ankieta_naglowek", "id_podzapytania"]