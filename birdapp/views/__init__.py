# views/__init__.py
# This file makes the views directory a Python package and imports all views

from .home_views import home, index
from .sighting_views import (
    add_sighting, search_birds, sighting_list, 
    SightingYearListView, sighting_year_redirect
)
from .bird_views import (
    bird, bird_list, bird_add, bird_edit, bird_detail, 
    bird_delete, bird_bulk_delete
)
from .family_views import (
    family_list, family_add, family_edit, family_delete
)
from .location_views import (
    location_sightings,  search_locations, location_add, location_edit,
    location_delete, location_list, location_detail,
    get_all_child_locations, location_bulk_delete
)
from .list_views import (
    lifelist, yearlist, monthlist, monthlist_year_redirect, monthlist_month_redirect
)
from .trip_views import (
    trip_list, trip_add, trip_detail, trip_edit, trip_delete
)

# Make all views available at package level for backwards compatibility
__all__ = [
    # Home views
    'home', 'index',
    
    # Sighting views
    'add_sighting', 'search_birds', 'sighting_list',
    'SightingYearListView', 'sighting_year_redirect',
    
    # Bird views
    'bird', 'bird_list', 'bird_add', 'bird_edit', 'bird_detail',
    'bird_delete', 'bird_bulk_delete',
    
    # Family views
    'family_list', 'family_add', 'family_edit', 'family_delete',
    
    # Location views
    'location_sightings', 'location_list', 'search_locations',
    'get_all_child_locations',  'location_add', 'location_edit',
    'location_delete', 'location_detail',  'location_bulk_delete',
    
    # List views
    'lifelist', 'yearlist', 'monthlist', 'monthlist_year_redirect', 'monthlist_month_redirect',

    # Trip views
    'trip_list', 'trip_add', 'trip_detail', 'trip_edit', 'trip_delete',
    
]