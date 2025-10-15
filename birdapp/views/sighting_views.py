# views/sighting_views.py
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse

from ..models import Sighting, Bird
from ..forms import SightingForm

def add_sighting(request):
    if request.method == 'POST':
        form = SightingForm(request.POST)
        if form.is_valid():
            sighting = form.save()
            messages.success(request, f'Sighting of {sighting.bird.english_name} recorded successfully!')
            return redirect('add_sighting')  # Redirect to clear form
        else:
            # Debug: Print form errors to see what's failing
            print("Form errors:", form.errors)
            print("Non-field errors:", form.non_field_errors())
            for field_name, field in form.fields.items():
                if field_name in form.errors:
                    print(f"Field '{field_name}' errors: {form.errors[field_name]}")
            
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SightingForm()
    
    return render(request, 'birdapp/add_sighting.html', {'form': form})

def search_birds(request):
    """AJAX endpoint to search birds by English name"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # Require at least 2 characters
        return JsonResponse({'birds': []})
    
    birds = Bird.objects.filter(
        english_name__icontains=query
    ).order_by('english_name')[:20]  # Limit to 20 results
    
    bird_data = [{
        'id': bird.id,
        'english_name': bird.english_name,
        'latin_name': bird.latin_name or '',
        'display_name': f"{bird.english_name}" + (f" ({bird.latin_name})" if bird.latin_name else "")
    } for bird in birds]
    
    return JsonResponse({'birds': bird_data})

# TODO: Refactor this view as a year list, not a sightings list
# TODO: Rename template to year_list.html
class SightingYearListView(ListView):
    model = Sighting
    template_name = 'year_list.html'  # If template is directly in birdapp/templates/
    context_object_name = 'sightings'
    paginate_by = 20
    
    def get_queryset(self):
        # Check for year in URL path first, then query parameters
        year = self.kwargs.get('year') or self.request.GET.get('year')
        
        if year:
            try:
                year = int(year)
                return Sighting.objects.filter(
                    date_seen__year=year
                ).select_related('bird', 'location', 'trip').order_by('-date_seen')
            except (ValueError, TypeError):
                pass
        
        # Return all sightings if no valid year
        return Sighting.objects.select_related('bird', 'location', 'trip').order_by('-date_seen')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get year from URL or query parameters
        year = self.kwargs.get('year') or self.request.GET.get('year')
        if year:
            try:
                context['year'] = int(year)
            except (ValueError, TypeError):
                context['year'] = None
        
        # Add available years for the filter dropdown
        context['available_years'] = Sighting.objects.dates('date_seen', 'year', order='DESC')
        return context

def sighting_list(request):
    """Main view that handles all sightings with optional year filtering"""
    year = request.GET.get('year')
    sightings = Sighting.objects.select_related('bird', 'location', 'trip')
    
    if year:
        try:
            year = int(year)
            sightings = sightings.filter(date_seen__year=year)
        except ValueError:
            year = None
    
    sightings = sightings.order_by('-date_seen')
    
    # Get available years for filter dropdown
    available_years = Sighting.objects.dates('date_seen', 'year', order='DESC')
    
    context = {
        'sightings': sightings,
        'year': year,
        'available_years': available_years,
    }
    return render(request, 'sightings/year_list.html', context)

def sighting_year_redirect(request, year):
    from django.shortcuts import redirect
    from django.urls import reverse
    
    url_with_params = reverse('sighting_list') + f'?year={year}'
    return redirect(url_with_params, permanent=True)

