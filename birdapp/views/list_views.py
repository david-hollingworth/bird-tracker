# views/list_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Max, Min

from ..models import Sighting, Bird, Location
from .location_views import get_all_child_locations

def locationlist(request, location_id=None):
    # Get location_id from URL parameter first, then from query parameter
    if location_id is None:
        location_id = request.GET.get('location')
    
    selected_location = None
    species_list = []
    child_locations = []
    total_species = 0
    page_obj = None
    
    if location_id:
        try:
            selected_location = get_object_or_404(Location, pk=location_id)
            
            # Get all child locations recursively
            child_locations = get_all_child_locations(selected_location)
            
            # Create list of all locations to include (parent + all children)
            all_locations = [selected_location] + child_locations
            location_ids = [loc.id for loc in all_locations]
            
            # Get distinct species for this location and its children with additional details
            species_sightings = Sighting.objects.filter(
                location_id__in=location_ids
            ).values('bird').annotate(
                first_seen=Min('date_seen'),
                last_seen=Max('date_seen'),
                total_sightings=Count('id')
            ).order_by('-last_seen')
            
            # Build the species list with bird details
            for entry in species_sightings:
                bird_id = entry['bird']
                first_seen_date = entry['first_seen']
                last_seen_date = entry['last_seen']
                sighting_count = entry['total_sightings']
                
                # Get the bird object
                bird = Bird.objects.get(pk=bird_id)
                
                # Get the first sighting for this bird at this location
                first_sighting = Sighting.objects.filter(
                    bird_id=bird_id,
                    location_id__in=location_ids,
                    date_seen=first_seen_date
                ).select_related('location', 'trip').first()
                
                # Get the most recent sighting for this bird at this location
                recent_sighting = Sighting.objects.filter(
                    bird_id=bird_id,
                    location_id__in=location_ids,
                    date_seen=last_seen_date
                ).select_related('location', 'trip').first()
                
                species_list.append({
                    'bird': bird,
                    'first_seen_date': first_seen_date,
                    'last_seen_date': last_seen_date,
                    'total_sightings': sighting_count,
                    'first_sighting': first_sighting,
                    'recent_sighting': recent_sighting,
                    'is_recent_only': first_seen_date == last_seen_date  # True if only seen once
                })
            
            total_species = len(species_list)
            
            # Pagination
            paginator = Paginator(species_list, 20)  # Show 20 species per page
            page_number = request.GET.get('page')
            
            try:
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                page_obj = paginator.page(1)
            except EmptyPage:
                # If page is out of range, deliver last page of results.
                page_obj = paginator.page(paginator.num_pages)
            
        except (ValueError, Location.DoesNotExist):
            pass
    
    context = {
        'selected_location': selected_location,
        'page_obj': page_obj,
        'species_list': page_obj.object_list if page_obj else species_list,
        'child_locations': child_locations,
        'total_species': total_species,
    }
    
    return render(request, 'birdapp/locationlist.html', context)

def yearlist(request):
    """Enhanced year list view with lifelist-style data display and pagination"""
    from django.core.paginator import Paginator
    
    year = request.GET.get('year')
    page_size = request.GET.get('page_size', '20')
    page = request.GET.get('page', 1)
    
    # Get base queryset for bird sightings
    base_sightings = Sighting.objects.select_related('bird', 'location', 'trip', 'bird__family')
    
    # Filter by year if specified
    if year:
        try:
            year = int(year)
            filtered_sightings = base_sightings.filter(date_seen__year=year)
        except (ValueError, TypeError):
            year = None
            filtered_sightings = base_sightings
    else:
        filtered_sightings = base_sightings
    
    # Get each bird's first and most recent sighting dates (within the filtered timeframe)
    bird_sightings = filtered_sightings.values('bird').annotate(
        first_seen=Min('date_seen'),
        last_seen=Max('date_seen')
    ).order_by('-last_seen')  # Order by most recently seen
    
    # Build the lifelist entries with details from first sighting
    lifelist_entries = []
    for entry in bird_sightings:
        bird_id = entry['bird']
        first_seen_date = entry['first_seen']
        last_seen_date = entry['last_seen']
        
        # Get the first sighting for this bird (within the filtered timeframe)
        first_sighting = filtered_sightings.filter(
            bird_id=bird_id,
            date_seen=first_seen_date
        ).select_related('bird', 'location', 'trip').first()
        
        if first_sighting:
            # Count total sightings for this bird (within the filtered timeframe)
            total_sightings = filtered_sightings.filter(bird_id=bird_id).count()
            
            lifelist_entries.append({
                'bird': first_sighting.bird,
                'first_sighting': first_sighting,
                'first_seen_date': first_seen_date,
                'last_seen_date': last_seen_date,
                'total_sightings': total_sightings,
                'is_recent': first_seen_date == last_seen_date  # True if only seen once in this timeframe
            })
    
    # Handle pagination
    page_obj = None
    is_paginated = False
    current_page_size = page_size
    
    if page_size != 'all':
        try:
            page_size = int(page_size)
            if page_size <= 0:
                page_size = 20
        except (ValueError, TypeError):
            page_size = 20
        
        paginator = Paginator(lifelist_entries, page_size)
        
        try:
            page_obj = paginator.page(page)
            lifelist_entries = page_obj.object_list
            is_paginated = paginator.num_pages > 1
        except Exception:
            page_obj = paginator.page(1)
            lifelist_entries = page_obj.object_list
            is_paginated = paginator.num_pages > 1
    
    # Calculate year statistics if year is specified
    year_stats = None
    if year:
        total_sightings = filtered_sightings.count()
        unique_species = len(bird_sightings)
        
        # Calculate new species for this year (species seen for the first time this year)
        # Get all species seen this year
        this_year_species = set(filtered_sightings.values_list('bird', flat=True))
        
        # Get species seen before this year
        previous_years_species = set(
            base_sightings.filter(
                date_seen__year__lt=year
            ).values_list('bird', flat=True)
        )
        
        # New species = species seen this year but not in previous years
        new_species = len(this_year_species - previous_years_species)
        
        year_stats = {
            'total_sightings': total_sightings,
            'unique_species': unique_species,
            'new_species': new_species
        }
    
    # Get available years with statistics
    available_years_with_counts = []
    years_data = base_sightings.values('date_seen__year').annotate(
        sighting_count=Count('id'),
        species_count=Count('bird', distinct=True)
    ).order_by('-date_seen__year')
    
    for year_data in years_data:
        available_years_with_counts.append({
            'year': year_data['date_seen__year'],
            'sighting_count': year_data['sighting_count'],
            'species_count': year_data['species_count']
        })
    
    # Get total species count for "All Years" option
    total_all_species = base_sightings.values('bird').distinct().count()
    
    context = {
        'lifelist_entries': lifelist_entries,
        'total_species': len(bird_sightings),  # Total before pagination
        'year': year,
        'year_stats': year_stats,
        'available_years_data': available_years_with_counts,
        'total_all_species': total_all_species,
        'page_obj': page_obj,
        'is_paginated': is_paginated,
        'current_page_size': current_page_size,
    }
    
    return render(request, 'birdapp/yearlist.html', context)

def lifelist(request):
    # Get page size from request, default to 20
    page_size = request.GET.get('page_size', '20')
    
    # Validate page_size
    valid_page_sizes = ['10', '20', '50', 'all']
    if page_size not in valid_page_sizes:
        page_size = '20'
    
    # Get each bird's first and most recent sighting dates
    bird_sightings = Sighting.objects.values('bird').annotate(
        first_seen=Min('date_seen'),
        last_seen=Max('date_seen')
    ).order_by('-last_seen')  # Order by most recently seen
    
    # Build the lifelist with details from first sighting
    lifelist_entries = []
    for entry in bird_sightings:
        bird_id = entry['bird']
        first_seen_date = entry['first_seen']
        last_seen_date = entry['last_seen']
        
        # Get the first sighting for this bird (oldest date)
        first_sighting = Sighting.objects.filter(
            bird_id=bird_id,
            date_seen=first_seen_date
        ).select_related('bird', 'location', 'trip').first()
        
        if first_sighting:
            # Count total sightings for this bird
            total_sightings = Sighting.objects.filter(bird_id=bird_id).count()
            
            lifelist_entries.append({
                'bird': first_sighting.bird,
                'first_sighting': first_sighting,
                'first_seen_date': first_seen_date,
                'last_seen_date': last_seen_date,
                'total_sightings': total_sightings,
                'is_recent': first_seen_date == last_seen_date  # True if only seen once
            })
    
    # Handle pagination
    total_species = len(lifelist_entries)
    
    if page_size == 'all':
        paginated_entries = lifelist_entries
        page_obj = None
        is_paginated = False
    else:
        page_size_int = int(page_size)
        paginator = Paginator(lifelist_entries, page_size_int)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.get_page(page_number)
            paginated_entries = page_obj.object_list
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)
            paginated_entries = page_obj.object_list
        
        is_paginated = paginator.num_pages > 1
    
    context = {
        'lifelist_entries': paginated_entries,
        'total_species': total_species,
        'page_obj': page_obj,
        'current_page_size': page_size,
        'valid_page_sizes': valid_page_sizes,
        'is_paginated': is_paginated,
    }
    
    return render(request, 'birdapp/lifelist.html', context)

def monthlist(request):
    """Enhanced month list view with year/month selection and pagination"""
    from django.core.paginator import Paginator
    import calendar
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    page_size = request.GET.get('page_size', '20')
    page = request.GET.get('page', 1)
    
    # Get base queryset for bird sightings
    base_sightings = Sighting.objects.select_related('bird', 'location', 'trip', 'bird__family')
    
    # Filter by year and month if specified
    filtered_sightings = base_sightings
    if year and month:
        try:
            year = int(year)
            month = int(month)
            if 1 <= month <= 12:
                filtered_sightings = base_sightings.filter(date_seen__year=year, date_seen__month=month)
            else:
                year = None
                month = None
        except (ValueError, TypeError):
            year = None
            month = None
    elif year:  # Year only, no month specified
        try:
            year = int(year)
            filtered_sightings = base_sightings.filter(date_seen__year=year)
            month = None
        except (ValueError, TypeError):
            year = None
            month = None
    
    # Get each bird's first and most recent sighting dates (within the filtered timeframe)
    bird_sightings = filtered_sightings.values('bird').annotate(
        first_seen=Min('date_seen'),
        last_seen=Max('date_seen')
    ).order_by('-last_seen')  # Order by most recently seen
    
    # Build the lifelist entries with details from first sighting
    lifelist_entries = []
    for entry in bird_sightings:
        bird_id = entry['bird']
        first_seen_date = entry['first_seen']
        last_seen_date = entry['last_seen']
        
        # Get the first sighting for this bird (within the filtered timeframe)
        first_sighting = filtered_sightings.filter(
            bird_id=bird_id,
            date_seen=first_seen_date
        ).select_related('bird', 'location', 'trip').first()
        
        if first_sighting:
            # Count total sightings for this bird (within the filtered timeframe)
            total_sightings = filtered_sightings.filter(bird_id=bird_id).count()
            
            # Check if this is a life list addition (first time ever seen this bird)
            is_lifelist_addition = not base_sightings.filter(
                bird_id=bird_id,
                date_seen__lt=first_seen_date
            ).exists()
            
            lifelist_entries.append({
                'bird': first_sighting.bird,
                'first_sighting': first_sighting,
                'first_seen_date': first_seen_date,
                'last_seen_date': last_seen_date,
                'total_sightings': total_sightings,
                'is_recent': first_seen_date == last_seen_date,  # True if only seen once in this timeframe
                'is_lifelist_addition': is_lifelist_addition,  # True if this is the very first sighting of this bird ever
            })
    
    # Handle pagination
    page_obj = None
    is_paginated = False
    current_page_size = page_size
    
    if page_size != 'all':
        try:
            page_size = int(page_size)
            if page_size <= 0:
                page_size = 20
        except (ValueError, TypeError):
            page_size = 20
        
        paginator = Paginator(lifelist_entries, page_size)
        
        try:
            page_obj = paginator.page(page)
            lifelist_entries = page_obj.object_list
            is_paginated = paginator.num_pages > 1
        except Exception:
            page_obj = paginator.page(1)
            lifelist_entries = page_obj.object_list
            is_paginated = paginator.num_pages > 1
    
    # Calculate month statistics if year and month are specified
    month_stats = None
    if year and month:
        total_sightings = filtered_sightings.count()
        unique_species = len(bird_sightings)
        
        # Calculate new species for this month (species seen for the first time this month)
        this_month_species = set(filtered_sightings.values_list('bird', flat=True))
        
        # Get species seen before this month
        from datetime import date
        month_start = date(year, month, 1)
        previous_species = set(
            base_sightings.filter(
                date_seen__lt=month_start
            ).values_list('bird', flat=True)
        )
        
        # New species = species seen this month but not before
        new_species = len(this_month_species - previous_species)
        
        month_stats = {
            'total_sightings': total_sightings,
            'unique_species': unique_species,
            'new_species': new_species
        }
    
    # Get available years and months with statistics
    available_data = {}
    months_data = base_sightings.values('date_seen__year', 'date_seen__month').annotate(
        sighting_count=Count('id'),
        species_count=Count('bird', distinct=True)
    ).order_by('-date_seen__year', '-date_seen__month')
    
    for month_data in months_data:
        year_key = month_data['date_seen__year']
        month_key = month_data['date_seen__month']
        
        if year_key not in available_data:
            available_data[year_key] = {
                'year': year_key,
                'months': {},
                'year_totals': {'sighting_count': 0, 'species_count': 0}
            }
        
        available_data[year_key]['months'][month_key] = {
            'month': month_key,
            'month_name': calendar.month_name[month_key],
            'sighting_count': month_data['sighting_count'],
            'species_count': month_data['species_count']
        }
        
        # Add to year totals
        available_data[year_key]['year_totals']['sighting_count'] += month_data['sighting_count']
    
    # Calculate unique species per year
    for year_key in available_data:
        year_species = base_sightings.filter(
            date_seen__year=year_key
        ).values('bird').distinct().count()
        available_data[year_key]['year_totals']['species_count'] = year_species
    
    # Convert to ordered list
    available_years_data = []
    for year_key in sorted(available_data.keys(), reverse=True):
        year_info = available_data[year_key]
        # Sort months in reverse chronological order
        sorted_months = []
        for month_num in sorted(year_info['months'].keys(), reverse=True):
            sorted_months.append(year_info['months'][month_num])
        year_info['months'] = sorted_months
        available_years_data.append(year_info)
    
    # Get total species count for "All Time" option
    total_all_species = base_sightings.values('bird').distinct().count()
    
    # Get month name for display
    month_name = None
    if month:
        month_name = calendar.month_name[month]
    
    context = {
        'lifelist_entries': lifelist_entries,
        'total_species': len(bird_sightings),  # Total before pagination
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_stats': month_stats,
        'available_years_data': available_years_data,
        'total_all_species': total_all_species,
        'page_obj': page_obj,
        'is_paginated': is_paginated,
        'current_page_size': current_page_size,
    }
    
    return render(request, 'birdapp/monthlist.html', context)

def monthlist_year_redirect(request, year):
    """Redirect year-based URLs to query parameter format"""
    return redirect(f"{reverse('monthlist')}?year={year}")

def monthlist_month_redirect(request, year, month):
    """Redirect month-based URLs to query parameter format"""
    return redirect(f"{reverse('monthlist')}?year={year}&month={month}")