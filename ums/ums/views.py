from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.apps import apps
from django.db.models import Model

def home_view(request):
    accessible_models = []

    excluded_app_labels = [
        'admin',       # Django Admin
        'auth',        # Django Authentication (User, Group, Permission models)
        'contenttypes',# Django ContentTypes
        'sessions',    # Django Sessions
        'staticfiles', # Django StaticFiles
    ]

    # Iterate through all installed apps
    for app_config in apps.get_app_configs():
        if app_config.label in excluded_app_labels:
            continue # Skip this app

        for model_class in app_config.get_models():
            # Skip abstract models, proxy models, or models without list views
            if model_class._meta.abstract or model_class._meta.proxy:
                continue

            # Ensure the model has a default manager (most do)
            if not issubclass(model_class, Model): # Added this check for robustness, though get_models() usually returns Model subclasses
                continue

            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name
            verbose_name_plural = model_class._meta.verbose_name_plural or f"{model_name}s"
            verbose_name_plural = verbose_name_plural.title()

            has_rud_access = False
            rud_perms = [
                f'{app_label}.change_{model_name}',
                f'{app_label}.delete_{model_name}',
                f'{app_label}.view_{model_name}',
            ]

            for perm in rud_perms:
                if request.user.has_perm(perm):
                    has_rud_access = True
                    break

            has_add_access = False
            if request.user.has_perm(f'{app_label}.add_{model_name}'):
                has_add_access = True

            if has_rud_access:
                try:
                    model_url = reverse(f'{app_label}:view_{model_name}')
                    accessible_models.append({
                        'name': verbose_name_plural,
                        'url': model_url,
                    })
                except NoReverseMatch:
                    pass # Continue to the next model
            elif has_add_access: # If no RUD access, check if user can add
                try:
                    model_url = reverse(f'{app_label}:add_{model_name}')
                    accessible_models.append({
                        'name': f'Add {verbose_name_plural}',
                        'url': model_url,
                    })
                except NoReverseMatch:
                    pass

    context = {
        'accessible_models': accessible_models
    }
    return render(request, 'home.html', context)