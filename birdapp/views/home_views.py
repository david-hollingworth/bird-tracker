from django.shortcuts import render
from datetime import date
from ..models import Sighting

def index(request):
    """Legacy index view - redirects to home"""
    most_recent_sightings = Sighting.objects.order_by('-date_seen')[:5]
    context = {"most_recent_sightings": most_recent_sightings}
    return render(request, "birdapp/index.html", context)

# Home page view with statistics
def home(request):
    today = date.today()
    current_year = today.year
    last_year = current_year - 1
    current_month = today.month
    last_month = current_month - 1 if current_month > 1 else 12
    
    # Calculate statistics
    # Life list - total unique bird species ever seen
    life_list_count = Sighting.objects.values('bird').distinct().count()
    
    # This year's species count
    this_year_count = Sighting.objects.filter(
        date_seen__year=current_year
    ).values('bird').distinct().count()
    
    # Last year's species count
    last_year_count = Sighting.objects.filter(
        date_seen__year=last_year
    ).values('bird').distinct().count()
    
    # This month's species count
    this_month_count = Sighting.objects.filter(
        date_seen__year=current_year,
        date_seen__month=current_month
    ).values('bird').distinct().count()

    # Last month's species count
    last_month_count = Sighting.objects.filter(
        date_seen__year=current_year if last_month != 12 else last_year,
        date_seen__month=last_month
    ).values('bird').distinct().count()
    
    # Today's sightings
    todays_sightings = Sighting.objects.filter(
        date_seen=today
    ).select_related('bird', 'location', 'trip').order_by('-id')
    
    context = {
        'life_list_count': life_list_count,
        'this_year_count': this_year_count,
        'last_year_count': last_year_count,
        'this_month_count': this_month_count,
        'last_month_count': last_month_count,
        'todays_sightings': todays_sightings,
        'today': today,
        'current_year': current_year,
        'last_year': last_year,
    }
    
    return render(request, 'birdapp/home.html', context)