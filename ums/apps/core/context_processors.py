from apps.organization.models import Faculty, Program

def organization_data(request):
    """
    Context processor to provide organization data to all templates.
    """
    context = {}
    if not request.user.is_authenticated:
        return context
        
    if request.user.has_perm('users.access_global'):
        # Global access - show all faculties and programs
        context['all_faculties'] = Faculty.objects.all()
        context['all_programs'] = Program.objects.all()
    else:
        # Faculty-wide access - show user's faculties and their programs
        user_faculties = request.user.faculties.all()
        context['all_faculties'] = user_faculties
        context['all_programs'] = Program.objects.filter(faculty__in=user_faculties).all()
    
    return context
