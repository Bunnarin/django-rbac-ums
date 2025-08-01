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
    # init
    s['permissions'] = s.get('permissions', [])
    s['selected_faculty'] = s.get('selected_faculty', 'None')
    s['selected_program'] = s.get('selected_program', 'None')
    # affiliation
    user_faculties = user.faculties.all()
    if 'access_global' in s['permissions']:
        context['all_faculties'] = Faculty.objects.all()
        context['all_programs'] = Program.objects.select_related('faculty').all()
    elif 'access_faculty_wide' in s['permissions']:
        context['all_faculties'] = user_faculties
        context['all_programs'] = Program.objects.select_related('faculty').filter(faculty__in=user_faculties)
    else:
        context['all_faculties'] = user_faculties
        context['all_programs'] = user.programs.select_related('faculty').all()
    
    return context
