from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    # path("bird/<int:birdid>/", views.bird, name="bird"),
    path("yearlist/", views.yearlist, name="yearlist"),
    path('sighting/add/', views.add_sighting, name='add_sighting'),
    path('api/search-birds/', views.search_birds, name='search_birds'),
    path('lifelist/', views.lifelist, name='lifelist'),
    # path('locations/', views.location_sightings, name='location_sightings'),
    path('api/search-locations/', views.search_locations, name='search_locations'),
    # Main sightings list - handles both all years and specific years via query params
    path('sightings/', views.sighting_list, name='sighting_list'),
    
    # Keep year-based URLs for SEO/bookmarking, but redirect to query-based
    path('sightings/<int:year>/', views.sighting_year_redirect, name='sightings_year'),

    # Location list URLs - specific location and general
    # Location management URLs
    path('locations/', views.location_list, name='location_list'),
    path('locations/add/', views.location_add, name='location_add'),
    path('locations/<int:location_id>/', views.location_detail, name='location_detail'),
    path('locations/<int:location_id>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:location_id>/delete/', views.location_delete, name='location_delete'),
    path('locations/bulk-delete/', views.location_bulk_delete, name='location_bulk_delete'),

    path('locationlist/<int:location_id>/', views.location_list, name='locationlist_with_id'),
    
    path('search-locations/', views.search_locations, name='search_locations'), 
    path('search-birds/', views.search_birds, name='search_birds'),

    # Add these URL patterns to your existing urls.py

    # Main monthlist view - handles both all time and specific year/month via query params
    path('monthlist/', views.monthlist, name='monthlist'),

    # Optional: SEO-friendly URLs for specific months (these can redirect to query-based URLs)
    path('monthlist/<int:year>/', views.monthlist_year_redirect, name='monthlist_year'),
    path('monthlist/<int:year>/<int:month>/', views.monthlist_month_redirect, name='monthlist_month'),

    # Bird management URLs
    path('birds/', views.bird_list, name='bird_list'),
    path('birds/add/', views.bird_add, name='bird_add'),
    path('birds/<int:bird_id>/', views.bird_detail, name='bird_detail'),
    path('birds/<int:bird_id>/edit/', views.bird_edit, name='bird_edit'),
    path('birds/<int:bird_id>/delete/', views.bird_delete, name='bird_delete'),
    path('birds/bulk-delete/', views.bird_bulk_delete, name='bird_bulk_delete'),
    
    # Family management URLs
    path('families/', views.family_list, name='family_list'),
    path('families/add/', views.family_add, name='family_add'),
    path('families/<int:family_id>/edit/', views.family_edit, name='family_edit'),
    path('families/<int:family_id>/delete/', views.family_delete, name='family_delete'),

    # Trip management URLs
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/add/', views.trip_add, name='trip_add'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:trip_id>/edit/', views.trip_edit, name='trip_edit'),
    path('trips/<int:trip_id>/delete/', views.trip_delete, name='trip_delete'),

]

