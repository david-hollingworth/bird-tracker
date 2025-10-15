from django.contrib import admin

# Register your models here.
from .models import Bird, Location, Sighting, Family, Trip

admin.site.register(Bird)
admin.site.register(Family)
admin.site.register(Location)
admin.site.register(Sighting)
admin.site.register(Trip)
