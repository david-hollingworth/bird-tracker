from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Min, Max
from ..models import Trip, Sighting
from datetime import datetime

def trip_list(request):
    """Display list of all trips with filtering and search"""
    trips = Trip.objects.all().annotate(
        sighting_count=Count('sighting'),
        first_sighting=Min('sighting__date_seen'),
        last_sighting=Max('sighting__date_seen')
    ).order_by('-start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        trips = trips.filter(
            Q(trip_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Year filter
    year_filter = request.GET.get('year', '')
    if year_filter:
        try:
            year = int(year_filter)
            trips = trips.filter(
                Q(start_date__year=year) | Q(end_date__year=year)
            )
        except ValueError:
            pass
    
    # Get all years for filter dropdown
    all_years = Trip.objects.dates('start_date', 'year', order='DESC')
    
    context = {
        'trips': trips,
        'search_query': search_query,
        'year_filter': year_filter,
        'all_years': all_years,
        'total_trips': trips.count(),
    }
    
    return render(request, 'birdapp/trip_list.html', context)


def trip_add(request):
    """Add a new trip"""
    if request.method == 'POST':
        trip_name = request.POST.get('trip_name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description', '')
        
        # Validation
        if not trip_name or not start_date or not end_date:
            messages.error(request, 'Trip name, start date, and end date are required.')
            return render(request, 'birdapp/trip_form.html', {
                'trip_name': trip_name,
                'start_date': start_date,
                'end_date': end_date,
                'description': description,
            })
        
        # Convert dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if end_date_obj < start_date_obj:
                messages.error(request, 'End date cannot be before start date.')
                return render(request, 'birdapp/trip_form.html', {
                    'trip_name': trip_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': description,
                })
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'birdapp/trip_form.html', {
                'trip_name': trip_name,
                'start_date': start_date,
                'end_date': end_date,
                'description': description,
            })
        
        trip = Trip.objects.create(
            trip_name=trip_name,
            start_date=start_date_obj,
            end_date=end_date_obj,
            description=description
        )
        
        messages.success(request, f'Trip "{trip_name}" added successfully!')
        return redirect('trip_detail', trip_id=trip.id)
    
    return render(request, 'birdapp/trip_form.html')


def trip_detail(request, trip_id):
    """Display trip details with associated sightings"""
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Get all sightings for this trip
    sightings = Sighting.objects.filter(trip=trip).select_related(
        'bird', 'location', 'bird__family'
    ).order_by('-date_seen', 'bird__english_name')
    
    # Calculate statistics
    unique_birds = sightings.values('bird').distinct().count()
    unique_locations = sightings.values('location').distinct().count()
    total_sightings = sightings.count()
    
    # Get date range of actual sightings
    if sightings.exists():
        first_sighting = sightings.aggregate(Min('date_seen'))['date_seen__min']
        last_sighting = sightings.aggregate(Max('date_seen'))['date_seen__max']
    else:
        first_sighting = None
        last_sighting = None
    
    context = {
        'trip': trip,
        'sightings': sightings,
        'unique_birds': unique_birds,
        'unique_locations': unique_locations,
        'total_sightings': total_sightings,
        'first_sighting': first_sighting,
        'last_sighting': last_sighting,
    }
    
    return render(request, 'birdapp/trip_detail.html', context)


def trip_edit(request, trip_id):
    """Edit an existing trip"""
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        trip_name = request.POST.get('trip_name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description', '')
        
        # Validation
        if not trip_name or not start_date or not end_date:
            messages.error(request, 'Trip name, start date, and end date are required.')
            return render(request, 'birdapp/trip_form.html', {
                'trip': trip,
                'trip_name': trip_name,
                'start_date': start_date,
                'end_date': end_date,
                'description': description,
            })
        
        # Convert dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if end_date_obj < start_date_obj:
                messages.error(request, 'End date cannot be before start date.')
                return render(request, 'birdapp/trip_form.html', {
                    'trip': trip,
                    'trip_name': trip_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': description,
                })
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'birdapp/trip_form.html', {
                'trip': trip,
                'trip_name': trip_name,
                'start_date': start_date,
                'end_date': end_date,
                'description': description,
            })
        
        trip.trip_name = trip_name
        trip.start_date = start_date_obj
        trip.end_date = end_date_obj
        trip.description = description
        trip.save()
        
        messages.success(request, f'Trip "{trip_name}" updated successfully!')
        return redirect('trip_detail', trip_id=trip.id)
    
    context = {
        'trip': trip,
        'is_edit': True,
    }
    
    return render(request, 'birdapp/trip_form.html', context)


def trip_delete(request, trip_id):
    """Delete a trip (dereferences associated sightings)"""
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        # Get count of associated sightings before deletion
        sighting_count = Sighting.objects.filter(trip=trip).count()
        trip_name = trip.trip_name
        
        # Dereference all sightings (set trip to None)
        Sighting.objects.filter(trip=trip).update(trip=None)
        
        # Delete the trip
        trip.delete()
        
        if sighting_count > 0:
            messages.success(
                request, 
                f'Trip "{trip_name}" deleted successfully. {sighting_count} sighting(s) have been dereferenced.'
            )
        else:
            messages.success(request, f'Trip "{trip_name}" deleted successfully.')
        
        return redirect('trip_list')
    
    # Get sighting count for confirmation page
    sighting_count = Sighting.objects.filter(trip=trip).count()
    
    context = {
        'trip': trip,
        'sighting_count': sighting_count,
    }
    
    return render(request, 'birdapp/trip_confirm_delete.html', context)