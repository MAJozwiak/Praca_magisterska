from rest_framework import serializers
from .models import Podmiot

class PodmiotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Podmiot
        fields = ['id', 'kod', 'nazwa'] # To wyślemy do Reacta