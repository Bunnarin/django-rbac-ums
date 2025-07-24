from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import View, ListView, DeleteView, CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from apps.organization.models import Faculty, Program
from django import forms

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
        queryset = super().get_queryset()
        
        # Apply RLS filtering if available
        if hasattr(self.model.objects, "for_user"):
            queryset = self.model.objects.for_user(self.request)
        
        # Get all potential foreign key fields from table_fields
        related_fields = set()
        for field in getattr(self, 'table_fields', []):
            # Add direct fields that might be foreign keys
            field = field.replace('.', '__')
            direct_field = field.split('__')[0]
            field_obj = self.model._meta.get_field(direct_field)
            direct_field_is_relation = field_obj.is_relation and field_obj.many_to_one and field_obj.concrete
            
            if ("__" in field):
                # default = true
                chained_field_is_relation = True
                field_model = field_obj.related_model
                chained_obj = field_model._meta.get_field(field.split('__')[1])
                chained_field_is_relation = chained_obj.is_relation and chained_obj.many_to_one and chained_obj.concrete
            
            if direct_field_is_relation and chained_field_is_relation:
                # add the chained field
                related_fields.add(field)
            # add the direct field anyway
            related_fields.add(direct_field)

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
        queryset = super().get_queryset()
        
        # Apply RLS filtering if available
        if hasattr(self.model.objects, "for_user"):
            queryset = self.model.objects.for_user(self.request)
        
        # Get all potential foreign key fields from table_fields
        related_fields = set()
        for field in getattr(self, 'table_fields', []):
            if '.' in field:
                # Handle chained attributes (e.g., 'schedule._class')
                parts = field.split('.')
                for i in range(len(parts) - 1):
                    related_fields.add('.'.join(parts[:i+1]))
            else:
                # Add direct fields that might be foreign keys
                try:
                    field_obj = self.model._meta.get_field(field)
                    if field_obj.is_relation and field_obj.many_to_one and field_obj.concrete:
                        related_fields.add(field)
                except:
                    continue
        
        # Apply select_related if we have any related fields
        if related_fields:
            queryset = queryset.select_related(*related_fields)
        
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
                    # make the default field name optional and add help text
                    if self.fields.get(field_name):
                        self.fields[field_name].required = False
                        self.fields[field_name].help_text = f"select this field if you do not wish to create another {field_name}"
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
        if hasattr(self.model.objects, 'for_user'):
            self.model.objects.for_user(request).delete()
        else:
            self.model.objects.all().delete()
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
