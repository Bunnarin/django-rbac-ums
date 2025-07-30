from apps.organization.models import Faculty, Program

def organization_data(request):
    """
    Context processor to provide organization data to all templates.
    """
    context = {}
    s = request.session
    user = request.user
    if not user.is_authenticated:
        return context
    # group
    context['all_groups'] = user.groups.all()
    s['permissions'] = s.get('permissions', [])
    # affiliation
    user_faculties = user.faculties.all()
    if 'users.access_global' in s['permissions']:
        context['all_faculties'] = Faculty.objects.all()
        context['all_programs'] = Program.objects.select_related('faculty').all()
    elif 'users.access_faculty_wide' in s['permissions']:
        context['all_faculties'] = user_faculties
        context['all_programs'] = Program.objects.select_related('faculty').filter(faculty__in=user_faculties)
    else:
        context['all_faculties'] = user_faculties
        context['all_programs'] = user.programs.select_related('faculty').all()
    
    return context
