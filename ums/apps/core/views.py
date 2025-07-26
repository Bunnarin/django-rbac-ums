from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import View, ListView, DeleteView, CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from apps.organization.models import Faculty, Program

class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    """
    model = None
    object_actions = []
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
        user = self.request.user
        
        # Add table configuration
        context['table_fields'] = self.table_fields
        
        # Set up URLs
        context["object_actions"] = {}
        for action, url in self.object_actions:
            permission = url.replace(':', '.')
            if user.has_perm(permission):
                context["object_actions"][action] = url
        
        context["actions"] = {}
        for action, url in self.actions:
            permission = url.replace(':', '.')
            if user.has_perm(permission):
                context["actions"][action] = url

        return context
        
    def get_queryset(self):
        queryset = self.model.objects.get_queryset(request=self.request)
        # Get all potential foreign key fields from table_fields
        related_fields = set()
        for field in getattr(self, 'table_fields', []):
            # Add direct fields that might be foreign keys
            field = field.replace('.', '__')
            direct_field = field.split('__')[0]
            field_obj = self.model._meta.get_field(direct_field)
            direct_field_is_relation = field_obj.is_relation and field_obj.many_to_one and field_obj.concrete
            
            if direct_field_is_relation:
                related_fields.add(direct_field)

            if ("__" in field) and direct_field_is_relation:
                # check if the chained field is also a relation
                field_model = field_obj.related_model
                chained_obj = field_model._meta.get_field(field.split('__')[1])
                if chained_obj.is_relation and chained_obj.many_to_one and chained_obj.concrete:
                    related_fields.add(field)
            
        # Apply select_related if we have any related fields
        if related_fields:
            queryset = queryset.select_related(*related_fields)
        
        return queryset

class BaseWriteView(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add or update an object.
    """
    pk_url_kwarg = 'pk'
    fields = '__all__'
    
    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')
    
    def get_queryset(self):
        return self.model.objects.get_queryset(request=self.request)
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return super().get_form_class()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # remove the faculty and program field cuz we gonna inject them instead
        form.fields.pop('faculty', None)
        form.fields.pop('program', None)
        # filter any related model with faculty and program
        s = self.request.session
        for field_name, field in form.fields.items():
            try: 
                related_model = self.model._meta.get_field(field_name).related_model
                related_model_fields = [f.name for f in related_model._meta.fields]
                if 'faculty' in related_model_fields:
                    field.queryset = field.queryset.filter(faculty_id=s['selected_faculty'])
                if 'program' in related_model_fields:
                    field.queryset = field.queryset.filter(program_id=s['selected_program'])
            except:
                continue
        return form
    
    def form_valid(self, form):
        if not hasattr(form, "instance"):
            return super().form_valid(form)

        s = self.request.session
        # set the faculty and program
        if s['selected_faculty'] != "None": 
            form.instance.faculty = Faculty.objects.get(pk=s['selected_faculty'])
        else: form.instance.faculty = None

        if s['selected_program'] != "None": 
            form.instance.program = Program.objects.get(pk=s['selected_program'])
        else: form.instance.program = None

        return super().form_valid(form)

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

class BaseBulkDeleteView(BaseWriteView, View):
    """
    Mixin for views that require permission to delete an object.
    """
    model = None
    template_name = 'core/generic_delete.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.delete_{self.model_name}']
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'object': f'{self.model._meta.verbose_name_plural}'})

    def post(self, request, *args, **kwargs):
        self.model.objects.get_queryset(request=request).delete()
        return redirect(f'{self.app_label}:view_{self.model_name}')

@require_POST
def set_faculty(request):
    """
    Set the selected faculty for the user.
    """    
    faculty_id = request.POST.get('faculty_id')
    s = request.session
    if faculty_id == "":
        s['selected_faculty'] = "None"
        s['selected_program'] = "None"
    else:
        faculty_id = int(faculty_id)
        user = request.user
        authorized = user.has_perm('users.access_global')
        if not authorized and \
            faculty_id not in user.faculties.values_list('id', flat=True):
            return JsonResponse({'error': 'Unauthorized faculty'}, status=403)
        s['selected_faculty'] = faculty_id

        # now set the program automatically
        if authorized:
            new_program = Program.objects.filter(faculty=faculty_id).first()
        else:
            new_program = user.programs.filter(faculty=faculty_id).first()
        s['selected_program'] = new_program.id

    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def set_program(request):
    """
    Set the selected program for the user.
    """
    program_id = request.POST.get('program_id')
    s = request.session
    if program_id == "":
        s['selected_program'] = "None"
    else:
        program_id = int(program_id)
        user = request.user
        authorized = user.has_perm('users.access_global') or user.has_perm('users.access_faculty_wide')
        if not authorized and program_id not in user.programs.values_list('id', flat=True):
            return JsonResponse({'error': 'Unauthorized program'}, status=403)
        s['selected_program'] = program_id
    return redirect(request.META.get('HTTP_REFERER', '/'))
