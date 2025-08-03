from django.contrib.auth.models import Group
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
    # if user.groups is not empty, we choose the first one
    if user.groups.exists() and not s.get('selected_group'):
        s['selected_group'] = user.groups.first().id
        s['permissions'] = list(Group.objects.get(id=s['selected_group']).permissions.all().values_list('codename', flat=True))
    
    s['permissions'] = s.get('permissions', [])

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
    
    # select the first affiliation if not empty
    if user_faculties.exists() and not s.get('selected_faculty'):
        s['selected_faculty'] = user_faculties.first().id
    if user.programs.exists() and not s.get('selected_program'):
        s['selected_program'] = user.programs.first().id
    
    return context
