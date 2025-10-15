# views/bird_views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from ..models import Bird, Family, Sighting
from ..forms import BirdForm, BirdSearchForm, BirdBulkDeleteForm

def bird(request, birdid):
    """Legacy bird detail view - redirects to new bird_detail"""
    bird_obj = get_object_or_404(Bird, pk=birdid)
    return render(request, "birdapp/birddetail.html", {"bird": bird_obj})

def bird_list(request):
    """List all birds with search and pagination"""
    form = BirdSearchForm(request.GET)
    birds = Bird.objects.select_related('family').order_by('english_name')
    
    # Apply filters if form is valid
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        family_filter = form.cleaned_data.get('family')
        
        if search_query:
            birds = birds.filter(
                Q(english_name__icontains=search_query) |
                Q(latin_name__icontains=search_query) |
                Q(french_name__icontains=search_query)
            )
        
        if family_filter:
            birds = birds.filter(family=family_filter)
    
    # Add sighting counts for each bird
    birds = birds.annotate(sighting_count=Count('sighting'))
    
    # Pagination
    paginator = Paginator(birds, 25)  # Show 25 birds per page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'birds': page_obj.object_list,
        'total_birds': birds.count(),
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'birdapp/bird_list.html', context)

def bird_add(request):
    """Add a new bird"""
    if request.method == 'POST':
        form = BirdForm(request.POST)
        if form.is_valid():
            bird_obj = form.save()
            messages.success(request, f'Bird "{bird_obj.english_name}" added successfully!')
            return redirect('bird_detail', bird_id=bird_obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BirdForm()
    
    context = {
        'form': form,
        'title': 'Add New Bird',
        'submit_text': 'Add Bird',
        'cancel_url': reverse('bird_list'),
    }
    
    return render(request, 'birdapp/bird_form.html', context)

def bird_edit(request, bird_id):
    """Edit an existing bird"""
    bird_obj = get_object_or_404(Bird, id=bird_id)
    
    if request.method == 'POST':
        form = BirdForm(request.POST, instance=bird_obj)
        if form.is_valid():
            bird_obj = form.save()
            messages.success(request, f'Bird "{bird_obj.english_name}" updated successfully!')
            return redirect('bird_detail', bird_id=bird_obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BirdForm(instance=bird_obj)
    
    context = {
        'form': form,
        'bird': bird_obj,
        'title': f'Edit {bird_obj.english_name}',
        'submit_text': 'Update Bird',
        'cancel_url': reverse('bird_detail', kwargs={'bird_id': bird_obj.id}),
    }
    
    return render(request, 'birdapp/bird_form.html', context)

def bird_detail(request, bird_id):
    """View bird details with sightings"""
    bird_obj = get_object_or_404(Bird, id=bird_id)
    
    # Get all sightings for this bird
    sightings = Sighting.objects.filter(bird=bird_obj).select_related(
        'location', 'trip'
    ).order_by('-date_seen')
    
    # Calculate statistics
    total_sightings = sightings.count()
    first_sighting = sightings.last()  # Oldest
    latest_sighting = sightings.first()  # Most recent
    
    # Get unique locations - using Python set to ensure uniqueness
    # This is more reliable than database distinct() in some cases
    all_location_names = [
        sighting.location.location_name for sighting in sightings 
        if sighting.location and sighting.location.location_name
    ]
    unique_locations = list(set(all_location_names))
    unique_locations.sort()  # Sort alphabetically for better display
    
    # Alternative approach using database distinct (commented out)
    # unique_locations = sightings.values_list('location__location_name', flat=True).distinct()
    # unique_locations = [loc for loc in unique_locations if loc]  # Remove None values
    
    # Debug: Print to console to see what we're getting
    # print(f"DEBUG: All locations: {all_location_names}")
    # print(f"DEBUG: Unique locations: {unique_locations}")
    # print(f"DEBUG: Total sightings: {total_sightings}")
    
    context = {
        'bird': bird_obj,
        'sightings': sightings,
        'total_sightings': total_sightings,
        'first_sighting': first_sighting,
        'latest_sighting': latest_sighting,
        'unique_locations': list(unique_locations),
    }
    
    return render(request, 'birdapp/bird_detail.html', context)

@require_POST
@csrf_protect
def bird_delete(request, bird_id):
    """Delete a bird (AJAX)"""
    bird_obj = get_object_or_404(Bird, id=bird_id)
    
    # Check if bird has sightings
    sighting_count = Sighting.objects.filter(bird=bird_obj).count()
    
    if sighting_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete "{bird_obj.english_name}" because it has {sighting_count} sighting(s). Please delete the sightings first.'
        })
    
    bird_name = bird_obj.english_name
    bird_obj.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Bird "{bird_name}" has been deleted successfully.'
    })

@require_POST
@csrf_protect
def bird_bulk_delete(request):
    """Bulk delete birds (AJAX)"""
    form = BirdBulkDeleteForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Invalid request.'
        })
    
    bird_ids = form.cleaned_data['selected_birds']
    birds = Bird.objects.filter(id__in=bird_ids)
    
    # Check for birds with sightings
    birds_with_sightings = []
    birds_to_delete = []
    
    for bird_obj in birds:
        sighting_count = Sighting.objects.filter(bird=bird_obj).count()
        if sighting_count > 0:
            birds_with_sightings.append(f'"{bird_obj.english_name}" ({sighting_count} sightings)')
        else:
            birds_to_delete.append(bird_obj)
    
    if birds_with_sightings:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete the following birds because they have sightings: {", ".join(birds_with_sightings)}. Please delete their sightings first.'
        })
    
    # Delete birds without sightings
    deleted_count = len(birds_to_delete)
    deleted_names = [bird_obj.english_name for bird_obj in birds_to_delete]
    
    for bird_obj in birds_to_delete:
        bird_obj.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully deleted {deleted_count} bird(s): {", ".join(deleted_names)}.'
    })