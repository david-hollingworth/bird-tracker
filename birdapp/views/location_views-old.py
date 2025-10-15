from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Max, Min

from ..models import Sighting, Bird, Location

def get_all_child_locations(location):
    """
    Recursively get all child locations for a given location.
    """
    # Get direct children using parent_location field
    children = Location.objects.filter(parent_location=location)
    all_children = list(children)
    
    # Recursively get children of children
    for child in children:
        all_children.extend(get_all_child_locations(child))
    
    return all_children

def location_sightings(request):
    location_id = request.GET.get('location')
    selected_location = None
    sightings = []
    child_locations = []
    total_sightings = 0
    unique_species = 0
    
    if location_id:
        try:
            selected_location = get_object_or_404(Location, pk=location_id)
            
            # Get all child locations recursively
            child_locations = get_all_child_locations(selected_location)
            
            # Create list of all locations to include (parent + all children)
            all_locations = [selected_location] + child_locations
            location_ids = [loc.id for loc in all_locations]
            
            # Get all sightings for this location and its children
            sightings = Sighting.objects.filter(
                location_id__in=location_ids
            ).select_related('bird', 'location', 'trip').order_by('-date_seen', '-id')
            
            # Calculate statistics
            total_sightings = sightings.count()
            unique_species = sightings.values('bird').distinct().count()
            
        except (ValueError, Location.DoesNotExist):
            pass
    
    context = {
        'selected_location': selected_location,
        'sightings': sightings,
        'child_locations': child_locations,
        'total_sightings': total_sightings,
        'unique_species': unique_species,
    }
    
    return render(request, 'birdapp/location_sightings.html', context)

def search_locations(request):
    """AJAX endpoint to search locations"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # Require at least 2 characters
        return JsonResponse({'locations': []})
    
    # Search using location_name field
    locations = Location.objects.filter(
        location_name__icontains=query
    ).order_by('location_name')[:20]  # Limit to 20 results
    
    location_data = [{
        'id': location.id,
        'name': location.location_name,
        'display_name': str(location)  # Uses the model's __str__ method
    } for location in locations]
    
    return JsonResponse({'locations': location_data})

