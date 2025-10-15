# views/family_views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from ..models import Family, Bird
from ..forms import FamilyForm

def family_list(request):
    """List all bird families"""
    families = Family.objects.annotate(
        bird_count=Count('bird')
    ).order_by('family_name')
    
    context = {
        'families': families,
    }
    
    return render(request, 'birdapp/family_list.html', context)

def family_add(request):
    """Add a new family"""
    if request.method == 'POST':
        form = FamilyForm(request.POST)
        if form.is_valid():
            family = form.save()
            messages.success(request, f'Family "{family.family_name}" added successfully!')
            return redirect('family_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FamilyForm()
    
    context = {
        'form': form,
        'title': 'Add New Family',
        'submit_text': 'Add Family',
        'cancel_url': reverse('family_list'),
    }
    
    return render(request, 'birdapp/family_form.html', context)

def family_edit(request, family_id):
    """Edit an existing family"""
    family = get_object_or_404(Family, id=family_id)
    
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            family = form.save()
            messages.success(request, f'Family "{family.family_name}" updated successfully!')
            return redirect('family_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FamilyForm(instance=family)
    
    context = {
        'form': form,
        'family': family,
        'title': f'Edit {family.family_name}',
        'submit_text': 'Update Family',
        'cancel_url': reverse('family_list'),
    }
    
    return render(request, 'birdapp/family_form.html', context)

@require_POST
@csrf_protect
def family_delete(request, family_id):
    """Delete a family (AJAX)"""
    family = get_object_or_404(Family, id=family_id)
    
    # Check if family has birds
    bird_count = Bird.objects.filter(family=family).count()
    
    if bird_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete "{family.family_name}" because it has {bird_count} bird(s). Please reassign or delete the birds first.'
        })
    
    family_name = family.family_name
    family.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Family "{family_name}" has been deleted successfully.'
    })