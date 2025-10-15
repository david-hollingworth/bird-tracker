# forms.py
from django import forms
from django.http import JsonResponse
from .models import Sighting, Bird, Location, Trip, Family

class SightingForm(forms.ModelForm):
    bird_search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for a bird...',
            'class': 'form-control',
            'id': 'bird-search',
            'autocomplete': 'off'
        }),
        label='Search For A Birdy'
    )
    
    class Meta:
        model = Sighting
        fields = ['bird', 'location', 'trip', 'date_seen', 'heard_not_seen', 'count', 'notes']
        widgets = {
            'bird': forms.Select(attrs={
                'class': 'form-control',
                'id': 'bird-select',
                'style': 'display: hidden;'  # Initially hidden
            }),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'trip': forms.Select(attrs={'class': 'form-control'}),
            'date_seen': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'heard_not_seen': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'activeCheck'
            }),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optional notes about the sighting...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bird'].required = True
        self.fields['bird'].empty_label = "Select a bird first by searching above"
        
        # Don't restrict queryset - let it include all birds
        # The frontend will handle the selection via search
        # But the form needs to be able to validate the selected bird
        pass  # Remove the queryset restriction
    
    def clean_bird(self):
        """Custom validation for bird field"""
        bird = self.cleaned_data.get('bird')
        if not bird:
            raise forms.ValidationError("Please select a bird by searching above.")
        return bird

class LocationSelectForm(forms.Form):
    location_search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search for a location...',
            'class': 'form-control',
            'id': 'location-search',
            'autocomplete': 'off'
        }),
        label='Search Location'
    )
    
    location = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'location-select',
            'style': 'display: none;'
        }),
        empty_label="Select a location by searching above"
    )


class BirdForm(forms.ModelForm):
    """Form for adding/editing birds"""
    
    class Meta:
        model = Bird
        fields = ['english_name', 'latin_name', 'french_name', 'species_status', 'family']
        widgets = {
            'english_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter English name',
                'required': True
            }),
            'latin_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter scientific name (optional)'
            }),
            'french_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter French name (optional)'
            }),
            'species_status': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Resident, Migrant, Vagrant (optional)'
            }),
            'family': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'english_name': 'English Name',
            'latin_name': 'Scientific Name',
            'french_name': 'French Name',
            'species_status': 'Species Status',
            'family': 'Family'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make family field optional with empty choice
        self.fields['family'].empty_label = "Select a family"
        self.fields['family'].required = False
  
        # Add help text
        self.fields['english_name'].help_text = "Common name in English (required)"
        self.fields['latin_name'].help_text = "Binomial scientific name (e.g., Turdus migratorius)"
        self.fields['species_status'].help_text = "Conservation or occurrence status (Optional)"
        # Make species_status field optional
        self.fields['species_status'].required = False

class BirdSearchForm(forms.Form):
    """Form for searching birds"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by English name, Latin name, or French name...',
            'id': 'bird-search-input'
        })
    )
    family = forms.ModelChoiceField(
        queryset=Family.objects.all().order_by('family_name'),
        required=False,
        empty_label="All families",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class BirdBulkDeleteForm(forms.Form):
    """Form for bulk deleting birds"""
    selected_birds = forms.CharField(widget=forms.HiddenInput())
    
    def clean_selected_birds(self):
        data = self.cleaned_data['selected_birds']
        try:
            bird_ids = [int(id) for id in data.split(',') if id]
            if not bird_ids:
                raise forms.ValidationError("No birds selected for deletion.")
            return bird_ids
        except ValueError:
            raise forms.ValidationError("Invalid bird selection.")

class FamilyForm(forms.ModelForm):
    """Form for adding/editing bird families"""
    
    class Meta:
        model = Family
        fields = ['family_name', 'subfamily_name']
        widgets = {
            'family_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter family name',
                'required': True
            }),
            'subfamily_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subfamily name (optional)'
            })
        }
        labels = {
            'family_name': 'Family Name',
            'subfamily_name': 'Subfamily Name'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['family_name'].help_text = "Taxonomic family name (e.g., Turdidae)"
        self.fields['subfamily_name'].help_text = "Taxonomic subfamily if applicable"
        self.fields['subfamily_name'].required = False

class SightingForm(forms.ModelForm):
    """Form for adding/editing sightings"""
    
    class Meta:
        model = Sighting
        fields = ['bird', 'location', 'trip', 'date_seen', 'heard_not_seen', 'count', 'notes']
        widgets = {
            'bird': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'location': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'trip': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_seen': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'heard_not_seen': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this sighting...'
            })
        }
        labels = {
            'bird': 'Bird Species',
            'location': 'Location',
            'trip': 'Trip (Optional)',
            'date_seen': 'Date Seen',
            'heard_not_seen': 'Heard Only',
            'count': 'Number of Birds',
            'notes': 'Notes'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make trip field optional
        self.fields['trip'].empty_label = "No trip (optional)"
        self.fields['trip'].required = False
        
        # Add help text
        self.fields['bird'].help_text = "Select the bird species you observed"
        self.fields['location'].help_text = "Where did you see this bird?"
        self.fields['heard_not_seen'].help_text = "Check if you only heard the bird but didn't see it"
        self.fields['count'].help_text = "How many individuals did you observe?"
        
        # Order querysets for better user experience
        self.fields['bird'].queryset = Bird.objects.all().order_by('english_name')
        self.fields['location'].queryset = Location.objects.all().order_by('location_name')
        self.fields['trip'].queryset = Trip.objects.all().order_by('-start_date')

# Optional: Location and Trip forms if you need them
class LocationForm(forms.ModelForm):
    """Form for adding/editing locations"""
    
    class Meta:
        model = Location
        fields = ['location_name', 'parent_location']
        widgets = {
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name',
                'required': True
            }),
            'parent_location': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'location_name': 'Location Name',
            'parent_location': 'Parent Location'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_location'].empty_label = "No parent location (top level)"
        self.fields['parent_location'].required = False
        self.fields['location_name'].help_text = "Name of this location"
        self.fields['parent_location'].help_text = "Optional: larger area this location is within"

class TripForm(forms.ModelForm):
    """Form for adding/editing trips"""
    
    class Meta:
        model = Trip
        fields = ['trip_name', 'start_date', 'end_date', 'description']
        widgets = {
            'trip_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter trip name',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this trip...'
            })
        }
        labels = {
            'trip_name': 'Trip Name',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'description': 'Description'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trip_name'].help_text = "Name for this birding trip"
        self.fields['description'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data
    
class LocationForm(forms.ModelForm):
    """Form for creating and editing locations"""
    
    class Meta:
        model = Location
        fields = ['location_name', 'parent_location']
        widgets = {
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name',
                'required': True
            }),
            'parent_location': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'location_name': 'Location Name',
            'parent_location': 'Parent Location (optional)',
        }
        help_texts = {
            'parent_location': 'Select a parent location to create a hierarchical structure (e.g., Country > State > City)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order parent locations alphabetically and show full path
        self.fields['parent_location'].queryset = Location.objects.all().order_by('location_name')
        self.fields['parent_location'].label_from_instance = lambda obj: obj.get_full_path_string()


class LocationSearchForm(forms.Form):
    """Form for searching and filtering locations"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search locations...',
        }),
        label='Search'
    )
    
    parent_location = forms.ModelChoiceField(
        queryset=Location.objects.all().order_by('location_name'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Parent Location',
        empty_label='All parent locations'
    )
    
    show_top_level_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Show only top-level locations'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show full path for parent location dropdown
        self.fields['parent_location'].label_from_instance = lambda obj: obj.get_full_path_string()


class LocationBulkDeleteForm(forms.Form):
    """Form for bulk deleting locations"""
    
    selected_locations = forms.ModelMultipleChoiceField(
        queryset=Location.objects.all(),
        widget=forms.MultipleHiddenInput(),
        required=True
    )