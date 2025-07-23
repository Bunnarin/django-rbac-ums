from apps.organization.models import Faculty, Program

def organization_data(request):
    """
    Context processor to provide organization data to all templates.
    """
    context = {}
    user = request.user
    if not user.is_authenticated:
        return context
    
    user_faculties = user.faculties.all()
    if user.has_perm('users.access_global'):
        context['all_faculties'] = Faculty.objects.all()
        context['all_programs'] = Program.objects.select_related('faculty').all()
    elif user.has_perm('users.access_faculty_wide'):
        context['all_faculties'] = user_faculties
        context['all_programs'] = Program.objects.select_related('faculty').filter(faculty__in=user_faculties)
    else:
        context['all_faculties'] = user_faculties
        context['all_programs'] = user.programs.select_related('faculty').all()
    
    return context
