from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import ListView, DeleteView, CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, reverse
from apps.organization.models import Faculty, Program
from django import forms

class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    """
    model = None
    cruds = ["add", "change", "delete"]
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
        
        # Set up URLs
        user = self.request.user
        for action in self.cruds:
            permission = f"{self.app_label}.{action}_{self.model_name}"
            if user.has_perm(permission):
                url = permission.replace('.', ':')  
                context[f"{action}_url"] = url
        
        # set up action URLs
        for action, url in self.actions:
            permission = url.replace(':', '.')
            if user.has_perm(permission):
                context["actions"] = {}
                context["actions"][action] = url

        return context
        
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply RLS filtering if available
        if hasattr(self.model.objects, "for_user"):
            queryset = self.model.objects.for_user(self.request)
        
        # Get all foreign key fields
        foreign_keys = [
            field.name for field in self.model._meta.get_fields()
            if field.is_relation and field.many_to_one and field.concrete
        ]
        
        # Apply select_related if we have any foreign keys
        if foreign_keys:
            queryset = queryset.select_related(*foreign_keys)
        
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
        queryset = super().get_queryset()
        
        # Apply RLS filtering if available
        if hasattr(self.model.objects, "for_user"):
            queryset = self.model.objects.for_user(self.request)
        
        # Get all foreign key fields
        foreign_keys = [
            field.name for field in self.model._meta.get_fields()
            if field.is_relation and field.many_to_one and field.concrete
        ]
        
        # Apply select_related if we have any foreign keys
        if foreign_keys:
            queryset = queryset.select_related(*foreign_keys)
        
        return queryset
    
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
                queryset = related_model.objects.all()
                
                # Check if the related model has faculty and program fields
                if 'faculty' in related_model_fields:
                    queryset = queryset.filter(faculty_id=s['selected_faculty'])
                if 'program' in related_model_fields:
                    queryset = queryset.filter(program_id=s['selected_program'])
                field.queryset = queryset
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
    
    def get_form_class(self):
        # allows for custom form_class
        if self.form_class:
            return self.form_class
        
        if not hasattr(self, 'flat_fields'):
            return super().get_form_class()
            
        # this intercept the default model form and make inject the flat fields 
        class DynamicForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = self.fields or '__all__'
                flat_fields = self.flat_fields
                
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for field_name, field_list in self.Meta.flat_fields:
                    # Get the model of the flat field
                    flat_field = self._meta.model._meta.get_field(field_name)
                    related_model = flat_field.related_model
                    # Add fields from the related model
                    for field in field_list:
                        self.fields[f'{field_name}__{field}'] = forms.CharField(
                            label=f"{field_name.capitalize()} {field.replace('_', ' ')}",
                            required=field in getattr(related_model._meta, 'required_fields', [])
                        )
                    # make the default field name optional
                    if self.fields.get(field_name):
                        self.fields[field_name].required = False
        return DynamicForm
        
    def form_valid(self, form):
        # Handle related objects before the main save
        if not hasattr(form.Meta, 'flat_fields'):
            return super().form_valid(form)
        for field_name, field_list in form.Meta.flat_fields:
            # if user select the flat field, then we don't parse the expanded fields
            if form.cleaned_data.get(field_name):
                continue
            # Get the model for the flat field
            flat_field = self.model._meta.get_field(field_name)
            related_model = flat_field.related_model
            # Get data for related model
            related_data = {}
            for field in field_list:
                form_field = f'{field_name}__{field}'
                if form_field in form.cleaned_data:
                    value = form.cleaned_data.pop(form_field)
                    if value == '':
                        value = None
                    related_data[field] = value
            
            # Create related object if we have data
            if related_data:
                related_obj = related_model.objects.create(**related_data)
                setattr(form.instance, field_name, related_obj)
        
        return super().form_valid(form)

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
    if faculty_id == "":
        request.session['selected_faculty'] = "None"
        request.session['selected_program'] = "None"
        return redirect(request.META.get('HTTP_REFERER', '/'))
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
    if program_id == "":
        request.session['selected_program'] = "None"
        return redirect(request.META.get('HTTP_REFERER', '/'))
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
