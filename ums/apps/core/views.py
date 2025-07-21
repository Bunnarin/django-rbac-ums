from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import ListView, DeleteView, CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from apps.organization.models import Program

class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    """
    model = None
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        user = self.request.user
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add table configuration
        context['table_fields'] = self.table_fields
        
        # Set up action URLs
        user = self.request.user
        for action in self.actions:
            permission = f"{self.app_label}.{action}_{self.model_name}"
            if user.has_perm(permission):
                url = permission.replace('.', ':')
                context[f"{action}_url"] = url

        return context
        
    def get_queryset(self):
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()

class BaseWriteView(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add or update an object.
    """
    pk_url_kwarg = 'pk'
    fields = '__all__'
    
    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')
    
    def get_queryset(self):
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not form.fields.get('faculty') or not form.fields.get('program'):
            return form
            
        form.fields['faculty'].initial = self.request.session.get('selected_faculty')
        form.fields['program'].initial = self.request.session.get('selected_program')
        user = self.request.user
        if user.has_perm('users.access_global'):
            return form
        elif user.has_perm('users.access_faculty_wide'):
            form.fields['faculty'].queryset = user.faculties.all()
            form.fields['program'].queryset = Program.objects.filter(faculty__in=user.faculties.all())
        else:
            form.fields['faculty'].queryset = user.faculties.all()
            form.fields['program'].queryset = user.programs.all()
    
        return form

class BaseCreateView(BaseWriteView, CreateView):
    """
    Mixin for views that require permission to add an object.
    """
    template_name = 'core/generic_form.html'
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

class BaseUpdateView(BaseWriteView, UpdateView):
    """
    Mixin for views that require permission to update an object.
    """
    template_name = 'core/generic_form.html'
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.change_{self.model_name}']
        
class BaseDeleteView(BaseWriteView, DeleteView):
    """
    Mixin for views that require permission to delete an object.
    """
    template_name = 'core/generic_delete.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.delete_{self.model_name}']

@require_POST
def set_faculty(request):
    """
    Set the selected faculty for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    faculty_id = request.POST.get('faculty_id')
    try:
        faculty_id = int(faculty_id)
    except:
        # don't set anything if invalid
        return redirect(request.META.get('HTTP_REFERER', '/'))
    user = request.user
    authorized = user.has_perm('users.access_global')
    if not authorized and faculty_id not in user.faculties.values_list('id', flat=True):
        return JsonResponse({'success': False, 'error': 'Unauthorized faculty'}, status=403)
    request.session['selected_faculty'] = faculty_id
    # now set the program as well
    if authorized:
        new_program = Program.objects.filter(faculty_id=faculty_id).first()
    else:
        new_program = user.programs.filter(faculty_id=faculty_id).first()
    if new_program:
        request.session['selected_program'] = new_program.id

    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def set_program(request):
    """
    Set the selected program for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    program_id = request.POST.get('program_id')
    try:
        program_id = int(program_id)
    except:
        # don't set anything if invalid
        return redirect(request.META.get('HTTP_REFERER', '/'))
    # Check if the program is in user's programs
    user = request.user
    authorized = user.has_perm('users.access_global') or user.has_perm('users.access_faculty_wide')
    if not authorized and program_id not in request.user.programs.values_list('id', flat=True):
        return JsonResponse({'success': False, 'error': 'Unauthorized program'}, status=403)
    request.session['selected_program'] = program_id
    return redirect(request.META.get('HTTP_REFERER', '/'))
