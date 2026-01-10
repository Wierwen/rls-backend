from django.contrib import admin

from .models import FHIRQuestionnaireModel


@admin.register(FHIRQuestionnaireModel)
class FHIRQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "condition_code", "created_at")
    search_fields = ("slug", "title", "condition_code")

