from django import forms
from django.forms import formset_factory
from django.urls import reverse_lazy
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.generic import View, ListView, DeleteView, CreateView, UpdateView
from django.contrib.auth.models import Group
from django.views.decorators.http import require_POST
from django.forms.models import modelform_factory
from django.shortcuts import redirect, render
from apps.organization.models import Faculty, Program
from apps.users.managers import UserRLSManager
from .managers import RLSManager

class BaseListView(ListView):
    """
    Base view for displaying a list of objects.
    """
    model = None
    object_actions = []
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def dispatch(self, request, *args, **kwargs):
        # check if permission in request.session['permission']
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        s = request.session
        if not any(perm in s['permissions'] for perm in [f'view_{self.model_name}', f'change_{self.model_name}', f'delete_{self.model_name}']):
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add table configuration
        context['table_fields'] = self.table_fields
        
        # Set up URLs
        context["object_actions"] = {}
        for action, url, permission in self.object_actions:
            # it can be None for when this view can derive the permission on its own
            if not permission:
                _, permission = url.split(':')
            if permission in self.request.session['permissions']:
                context["object_actions"][action] = url
        
        context["actions"] = {}
        for action, url, permission in self.actions:
            if not permission:
                _, permission = url.split(':')
            if permission in self.request.session['permissions']:
                context["actions"][action] = url

        return context
        
    def get_queryset(self):
        # filter RLS sin
        if issubclass(self.model.objects.__class__, RLSManager) or \
            issubclass(self.model.objects.__class__, UserRLSManager):
            queryset = self.model.objects.get_queryset(request=self.request)
        else:
            queryset = super().get_queryset()
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

class BaseWriteView():
    """
    Mixin for views that require permission to add or update an object.
    """
    pk_url_kwarg = 'pk'
    fields = '__all__'
    template_name = 'core/generic_form.html'
    permission_required = []
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        for action, model in self.permission_required:
            if not model:
                model = self.model_name
            if not any(perm in request.session['permissions'] for perm in [f'{action}_{model}']):
                raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        if self.success_url:
            return self.success_url
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy(f'{self.app_label}:view_{self.model_name}')
        return context
    
    def get_queryset(self):
        if issubclass(self.model.objects.__class__, RLSManager) or \
            issubclass(self.model.objects.__class__, UserRLSManager):
            return self.model.objects.get_queryset(request=self.request)
        return super().get_queryset()
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        return super().get_form_class()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # remove the faculty and program field cuz we gonna inject them instead
        if form.fields.get('faculty'):
            form.fields.pop('faculty')
        if form.fields.get('program'):
            form.fields.pop('program')
        # filter the field if it has affiliation
        for field in form.fields:
            try: related_model = self.model._meta.get_field(field).related_model
            except: continue
            if not related_model:
                continue
            if issubclass(related_model.objects.__class__, RLSManager) or \
                issubclass(related_model.objects.__class__, UserRLSManager):
                form.fields[field].queryset = related_model.objects.get_queryset(request=self.request)
        return form
    
    def form_valid(self, form):
        if not hasattr(form, "instance"):
            return super().form_valid(form)

        # inject the faculty and program
        s = self.request.session
        
        if s['selected_faculty'] == "None": 
            form.instance.faculty = None
        else: 
            form.instance.faculty = Faculty.objects.get(pk=s['selected_faculty'])

        if s['selected_program'] == "None": 
            form.instance.program = None
        else: 
            form.instance.program = Program.objects.get(pk=s['selected_program'])

        return super().form_valid(form)

class BaseCreateView(BaseWriteView, CreateView):
    """
    Mixin for views that require permission to add an object.
    """
    permission_required = [('add', None)]

class BaseUpdateView(BaseWriteView, UpdateView):
    """
    Mixin for views that require permission to update an object.
    """
    permission_required = [('change', None)]
        
class BaseDeleteView(BaseWriteView, DeleteView):
    """
    Mixin for views that require permission to delete an object.
    """
    permission_required = [('delete', None)]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['title'] = f"are you sure you want to delete {obj}?"
        return context

class BaseBulkDeleteView(BaseWriteView, View):
    """
    Mixin for views that require permission to delete an object.
    """
    model = None
    template_name = 'core/generic_form.html'
    permission_required = [('delete', None)]
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'object': f'{self.model._meta.verbose_name_plural}'})

    def post(self, request, *args, **kwargs):
        self.model.objects.get_queryset(request=request).delete()
        return redirect(f'{self.app_label}:view_{self.model_name}')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"are you sure you want to delete all these {self.model_name}s?"
        return context

class BaseImportView(BaseCreateView):
    """
    Mixin for views that require permission to import an object.
    first, it will give a model form that asks the user to fill out the default value of each field.
    they can also paste an entire row of values where x is the row number
    then once they submit, we give them another form that autogenerate x amount of form (in row format)
    those rows of form comes with prefilled default that they input and they can modify it
    finally, they can submit the form and it will bulk create all the objects
    """

    def _get_default_form(self, request_post=None):
        form_class = self.form_class or modelform_factory(self.model, fields=self.fields)
        form = form_class(request_post or None, request=self.request)
        for field in form.fields:
            form.fields[field].required = False
            try: field_instance = self.model._meta.get_field(field)
            except: 
                if not isinstance(form.fields[field], forms.BooleanField):
                    form.fields[field].widget = forms.Textarea()
                continue
            if not field_instance.is_relation and not isinstance(form.fields[field], forms.BooleanField):
                form.fields[field].widget = forms.Textarea()
        return form
    
    def get(self, request, *args, **kwargs):
        default_form = self._get_default_form()
        return render(request, self.template_name, {'form': default_form, 'title': 'set the default values'})
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        FormSet_Class = formset_factory(
            self.form_class or modelform_factory(self.model, fields=self.fields),
            extra=0, can_delete=True
        )
        if 'form-TOTAL_FORMS' not in request.POST:
            form = self._get_default_form(request.POST)
            if form.is_valid():
                # calculating the num form
                data = form.cleaned_data
                max_row_num = 0
                for field in form.fields:
                    try: data[field] = data[field].split('\n')
                    except: continue
                    max_row_num = max(max_row_num, len(data[field]))
                
                # now populating the inital 
                initials = []         
                for i in range(max_row_num):
                    initials.append({})
                    for field in form.fields:
                        # if cleaned_data is an array, use the indexed. else, just use its default value
                        if isinstance(data[field], list) and len(data[field]) > 1:
                            try: initials[i][field] = data[field][i]
                            except IndexError: continue    
                        elif isinstance(data[field], list) and len(data[field]) == 1:
                            initials[i][field] = data[field][0]
                        else:
                            initials[i][field] = data[field]

                formset = FormSet_Class(initial=initials, form_kwargs={'request': request})
                return render(request, self.template_name, {'formset': formset})
            return render(request, self.template_name, {'form': form})
        
        elif 'form-TOTAL_FORMS' in request.POST:
            formset = FormSet_Class(request.POST, form_kwargs={'request': request})
            instances = []
            if formset.is_valid():
                for form in formset:
                    instance = form.save(commit=False)
                    instance.clean()
                    instances.append(instance)
                self.model.objects.bulk_create(instances)   
            return render(request, self.template_name, {'formset': formset})
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
        authorized = 'access_global' in s['permissions']
        if not authorized and faculty_id not in user.faculties.values_list('id', flat=True):
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
        authorized = 'access_global' in s['permissions'] or 'access_faculty_wide' in s['permissions']
        if not authorized and program_id not in user.programs.values_list('id', flat=True):
            return JsonResponse({'error': 'Unauthorized program'}, status=403)
        s['selected_program'] = program_id
    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def set_group(request):
    """
    Set the selected group for the user.
    """
    group_id = request.POST.get('group_id')
    s = request.session
    if group_id == "":
        s['selected_group'] = "None"
        s['permissions'] = []
    else:
        group_id = int(group_id)
        user = request.user
        if group_id not in user.groups.values_list('id', flat=True):
            return JsonResponse({'error': 'Unauthorized group'}, status=403)
        s['selected_group'] = group_id
        s['permissions'] = list(Group.objects.get(id=group_id).permissions.all().values_list('codename', flat=True))
    return redirect(request.META.get('HTTP_REFERER', '/'))
