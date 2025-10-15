import datetime
from django.utils import timezone
from django.db import models

# Create your models here.
class Bird(models.Model):
    english_name = models.CharField(max_length=200)
    latin_name = models.CharField(max_length=200, null=True)
    french_name = models.CharField(max_length=200, null=True, blank=True)
    species_status = models.CharField(max_length=200, null=True)
    family = models.ForeignKey('Family', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.english_name

class Location(models.Model):
    location_name = models.CharField(max_length=200)
    parent_location = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['location_name']

    def __str__(self):
        """Return a hierarchical string representation of the location"""
        # if self.parent_location:
            # return f"{self.parent_location} > {self.location_name}"
        return self.location_name
    
    def get_full_path(self):
        """Get the full hierarchical path as a list"""
        path = [self.location_name]
        parent = self.parent_location
        while parent:
            path.insert(0, parent.location_name)
            parent = parent.parent_location
        return path
    
    def get_full_path_string(self):
        """Get the full hierarchical path as a string"""
        return " > ".join(self.get_full_path())
    
    def get_ancestors(self):
        """Get all parent locations as objects in order from root to immediate parent"""
        ancestors = []
        parent = self.parent_location
        while parent:
            ancestors.insert(0, parent)
            parent = parent.parent_location
        return ancestors
    
class Trip(models.Model):
    trip_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.trip_name

    def duration(self):
        return (self.end_date - self.start_date).days + 1

class Sighting(models.Model):
    bird = models.ForeignKey(Bird, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    date_seen = models.DateField()
    heard_not_seen = models.BooleanField(default=False)
    count = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.bird} at {self.location} on {self.date_seen}"
    
    def was_seen_recently(self):
        return self.date_seen >= timezone.now().date() - datetime.timedelta(days=3)
    
    def was_seen_this_month(self):
        return self.date_seen >= timezone.now().date() - datetime.timedelta(days=30)
    
    def was_seen_this_year(self):
        return self.date_seen >= timezone.now().date() - datetime.timedelta(days=365)

class Family(models.Model):
    family_name = models.CharField(max_length=200)
    subfamily_name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.family_name} - {self.subfamily_name if self.subfamily_name else ''}"

