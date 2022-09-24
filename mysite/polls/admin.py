import base64
import json

import google.protobuf.timestamp_pb2
from django.contrib import admin
from django.core import serializers
from django.db import transaction

from polls.models import Choice, Outbox, Question

# from google.protobuf.internal.well_known_types import Timestamp


# from proto.question_pb2 import Question as QuestionProto


class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date Information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.create_outbox(obj)

    def create_outbox(self, obj):
        # proto_time_stamp = Timestamp()
        # proto_time_stamp.FromDatetime(obj.pub_date)
        #
        # proto = QuestionProto()
        # question = serializers.serialize("json", obj)
        question = {
            "id": obj.id,
            "question_text": obj.question_text,
            "pub_date": str(obj.pub_date),
        }

        outbox = Outbox(
            aggregatetype="question",
            aggregateid=obj.id,
            type="question_created",
            payload=json.dumps(question).encode(),
        )
        outbox.save()
        pass


# Register your models here.
admin.site.register(Question, QuestionAdmin)
