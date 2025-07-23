from apps.organization.models import Faculty, Program

def organization_data(request):
    """
    Context processor to provide organization data to all templates.
    """
    context = {}
    user = request.user
    if not user.is_authenticated:
        return context
        
    if user.has_perm('users.access_global'):
        context['all_faculties'] = Faculty.objects.all()
        context['all_programs'] = Program.objects.all()
    elif user.has_perm('users.access_faculty_wide'):
        context['all_faculties'] = user.faculties.all()
        context['all_programs'] = Program.objects.select_related('faculty').filter(faculty__in=user.faculties.all())
    else:
        context['all_faculties'] = user.faculties.all()
        context['all_programs'] = user.programs.all()
    
    return context
