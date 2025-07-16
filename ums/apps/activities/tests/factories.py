import json
import factory
from factory import Faker, SubFactory, LazyAttribute, post_generation
from factory.django import DjangoModelFactory, FileField
from django.contrib.auth import get_user_model
from apps.organization.tests.factories import FacultyFactory
from apps.users.tests.factories import UserFactory
from ..models import ActivityTemplate, Activity

User = get_user_model()

class ActivityTemplateFactory(DjangoModelFactory):
    class Meta:
        model = ActivityTemplate
        django_get_or_create = ('name',)

    name = Faker('sentence', nb_words=4)
    template_json = json.dumps([
        {
           "label": Faker('sentence'),
           "type": question_type,
           "required": True,
           "choices": [Faker('word') for _ in range(3)] 
        }
    for question_type in ["text", "paragraph", "integer", "decimal", "dropdown", "checkbox", "date"]])


class ActivityFactory(DjangoModelFactory):
    class Meta:
        model = Activity

    template = SubFactory(ActivityTemplateFactory)
    author = SubFactory(UserFactory)
    faculty = SubFactory(FacultyFactory)
    response_json = factory.LazyAttribute(lambda o: {
        "sections": [{
            "name": section["name"],
            "responses": [{
                "response": _generate_response(question)
                for question in section["questions"]
            }]
        } for section in o.template.template_json["sections"]]
    })

def _generate_response(question):
    question_type = question.get("type")
    if question_type == "text":
        return Faker('sentence', nb_words=8).generate({})
    elif question_type == "integer":
        return str(Faker('random_int', min=1, max=10).generate({}))
    elif question_type in ["select", "checkbox"]:
        if question.get("choices"):
            return Faker('random_element', elements=question["choices"]).generate({})
    elif question_type == "date":
        return Faker('date_this_year').generate({}).strftime('%Y-%m-%d')
    elif question_type == "email":
        return Faker('email').generate({})
    elif question_type == "url":
        return Faker('url').generate({})
    elif question_type == "decimal":
        return str(Faker('random_float', min=1, max=10).generate({}))