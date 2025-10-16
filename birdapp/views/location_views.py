# views/location_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from ..models import Location, Sighting
from ..forms import LocationForm, LocationSearchForm, LocationBulkDeleteForm


def get_all_child_locations(location):
    """Recursively get all child locations"""
    children = list(Location.objects.filter(parent_location=location))
    all_children = children.copy()
    
    for child in children:
        all_children.extend(get_all_child_locations(child))
    
    return all_children


def location_list(request):
    """List all locations with search and pagination"""
    form = LocationSearchForm(request.GET)
    locations = Location.objects.select_related('parent_location').order_by('location_name')
    
    # Apply filters if form is valid
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        parent_filter = form.cleaned_data.get('parent_location')
        show_top_level = form.cleaned_data.get('show_top_level_only')
        
        if search_query:
            locations = locations.filter(
                Q(location_name__icontains=search_query)
            )
        
        if parent_filter:
            locations = locations.filter(parent_location=parent_filter)
        
        if show_top_level:
            locations = locations.filter(parent_location__isnull=True)
    
    # Add sighting counts and child counts for each location
    locations = locations.annotate(
        sighting_count=Count('sighting', distinct=True)
    )
    
    # Add child location counts (must be done in Python since it's recursive)
    location_list = []
    for loc in locations:
        children = Location.objects.filter(parent_location=loc)
        loc.child_count = children.count()
        location_list.append(loc)
    
    # Pagination
    paginator = Paginator(location_list, 25)  # Show 25 locations per page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'locations': page_obj.object_list,
        'total_locations': len(location_list),
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'birdapp/location_list.html', context)


def location_add(request):
    """Add a new location"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location_obj = form.save()
            messages.success(request, f'Location "{location_obj.location_name}" added successfully!')
            return redirect('location_detail', location_id=location_obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill parent location if provided in query params
        parent_id = request.GET.get('parent')
        initial = {}
        if parent_id:
            try:
                parent = Location.objects.get(id=parent_id)
                initial['parent_location'] = parent
            except Location.DoesNotExist:
                pass
        
        form = LocationForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Add New Location',
        'submit_text': 'Add Location',
        'cancel_url': reverse('location_list'),
    }
    
    return render(request, 'birdapp/location_form.html', context)


def location_edit(request, location_id):
    """Edit an existing location"""
    location_obj = get_object_or_404(Location, id=location_id)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location_obj)
        if form.is_valid():
            # Check for circular parent reference
            new_parent = form.cleaned_data.get('parent_location')
            if new_parent:
                # Check if the new parent is a descendant of this location
                current = new_parent
                while current:
                    if current.id == location_obj.id:
                        messages.error(request, 'Cannot set parent location: this would create a circular reference.')
                        context = {
                            'form': form,
                            'location': location_obj,
                            'title': f'Edit {location_obj.location_name}',
                            'submit_text': 'Update Location',
                            'cancel_url': reverse('location_detail', kwargs={'location_id': location_obj.id}),
                        }
                        return render(request, 'birdapp/location_form.html', context)
                    current = current.parent_location
            
            location_obj = form.save()
            messages.success(request, f'Location "{location_obj.location_name}" updated successfully!')
            return redirect('location_detail', location_id=location_obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LocationForm(instance=location_obj)
    
    context = {
        'form': form,
        'location': location_obj,
        'title': f'Edit {location_obj.location_name}',
        'submit_text': 'Update Location',
        'cancel_url': reverse('location_detail', kwargs={'location_id': location_obj.id}),
    }
    
    return render(request, 'birdapp/location_form.html', context)


def location_detail(request, location_id):
    """View location details with sightings and child locations"""
    location_obj = get_object_or_404(Location, id=location_id)
    
    # Build breadcrumb path with location objects
    breadcrumb_path = []
    current = location_obj
    while current:
        breadcrumb_path.insert(0, current)
        current = current.parent_location
    
    # Get direct child locations
    child_locations = Location.objects.filter(
        parent_location=location_obj
    ).order_by('location_name')
    
    # Calculate recursive sighting counts for each child
    child_locations_with_counts = []
    for child in child_locations:
        # Get all descendants of this child
        all_child_descendants = get_all_child_locations(child)
        all_child_location_ids = [child.id] + [loc.id for loc in all_child_descendants]
        
        # Count sightings for this child and all its descendants
        child.sighting_count = Sighting.objects.filter(
            location_id__in=all_child_location_ids
        ).count()
        
        child_locations_with_counts.append(child)
    
    # Get all child locations recursively for the current location
    all_child_locations = get_all_child_locations(location_obj)
    all_location_ids = [location_obj.id] + [loc.id for loc in all_child_locations]
    
    # Get sightings for this location and all children
    sightings = Sighting.objects.filter(
        location_id__in=all_location_ids
    ).select_related('bird', 'location', 'trip').order_by('-date_seen')
    
    # Calculate statistics
    total_sightings = sightings.count()
    unique_species = sightings.values('bird').distinct().count()
    first_sighting = sightings.last()  # Oldest
    latest_sighting = sightings.first()  # Most recent
    
    # Get recent sightings (last 10)
    recent_sightings = sightings[:10]
    
    context = {
        'location': location_obj,
        'breadcrumb_path': breadcrumb_path,  # Add this
        'child_locations': child_locations_with_counts,
        'direct_children_count': len(child_locations_with_counts),
        'total_child_locations': len(all_child_locations),
        'sightings': recent_sightings,
        'total_sightings': total_sightings,
        'unique_species': unique_species,
        'first_sighting': first_sighting,
        'latest_sighting': latest_sighting,
    }
    
    return render(request, 'birdapp/location_detail.html', context)


@require_POST
@csrf_protect
def location_delete(request, location_id):
    """Delete a location (AJAX)"""
    location_obj = get_object_or_404(Location, id=location_id)
    
    # Check if location has sightings
    sighting_count = Sighting.objects.filter(location=location_obj).count()
    
    if sighting_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete "{location_obj.location_name}" because it has {sighting_count} sighting(s). Please delete or reassign the sightings first.'
        })
    
    # Check if location has child locations
    child_count = Location.objects.filter(parent_location=location_obj).count()
    
    if child_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete "{location_obj.location_name}" because it has {child_count} child location(s). Please delete or reassign the child locations first.'
        })
    
    location_name = location_obj.location_name
    location_obj.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Location "{location_name}" has been deleted successfully.'
    })


@require_POST
@csrf_protect
def location_bulk_delete(request):
    """Bulk delete locations (AJAX)"""
    form = LocationBulkDeleteForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Invalid request.'
        })
    
    location_ids = form.cleaned_data['selected_locations']
    locations = Location.objects.filter(id__in=location_ids)
    
    # Check for locations with sightings or children
    locations_with_sightings = []
    locations_with_children = []
    locations_to_delete = []
    
    for location_obj in locations:
        sighting_count = Sighting.objects.filter(location=location_obj).count()
        child_count = Location.objects.filter(parent_location=location_obj).count()
        
        if sighting_count > 0:
            locations_with_sightings.append(f'"{location_obj.location_name}" ({sighting_count} sightings)')
        elif child_count > 0:
            locations_with_children.append(f'"{location_obj.location_name}" ({child_count} children)')
        else:
            locations_to_delete.append(location_obj)
    
    error_messages = []
    if locations_with_sightings:
        error_messages.append(f'Cannot delete locations with sightings: {", ".join(locations_with_sightings)}')
    if locations_with_children:
        error_messages.append(f'Cannot delete locations with child locations: {", ".join(locations_with_children)}')
    
    if error_messages:
        return JsonResponse({
            'success': False,
            'message': '. '.join(error_messages) + '. Please delete or reassign them first.'
        })
    
    # Delete locations without sightings or children
    deleted_count = len(locations_to_delete)
    deleted_names = [location_obj.location_name for location_obj in locations_to_delete]
    
    for location_obj in locations_to_delete:
        location_obj.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully deleted {deleted_count} location(s): {", ".join(deleted_names)}.'
    })


# Add this to your location_views.py file (or update if it already exists)

def search_locations(request):
    """AJAX endpoint to search locations by name"""
    from django.http import JsonResponse
    from ..models import Location
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # Require at least 2 characters
        return JsonResponse({'locations': []})
    
    locations = Location.objects.filter(
        location_name__icontains=query
    ).select_related('parent_location').order_by('location_name')[:20]  # Limit to 20 results
    
    location_data = [{
        'id': location.id,
        'location_name': location.location_name,
        'full_path': location.get_full_path_string(),
        'display_name': location.get_full_path_string()
    } for location in locations]
    
    return JsonResponse({'locations': location_data})


def location_sightings(request):
    """View all sightings for a specific location (from query params)"""
    location_id = request.GET.get('location')
    
    if not location_id:
        # If no location specified, redirect to location list
        return redirect('location_list')
    
    location_obj = get_object_or_404(Location, id=location_id)
    
    # Get all child locations recursively
    child_locations = get_all_child_locations(location_obj)
    all_locations = [location_obj] + child_locations
    location_ids = [loc.id for loc in all_locations]
    
    # Get all sightings for this location and its children
    sightings = Sighting.objects.filter(
        location_id__in=location_ids
    ).select_related('bird', 'location', 'trip').order_by('-date_seen')
    
    # Pagination
    paginator = Paginator(sightings, 50)  # Show 50 sightings per page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)
    
    context = {
        'location': location_obj,
        'child_locations': child_locations,
        'page_obj': page_obj,
        'sightings': page_obj.object_list,
        'total_sightings': sightings.count(),
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'birdapp/location_sightings.html', context)