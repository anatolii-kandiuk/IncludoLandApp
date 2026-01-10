from django.contrib import admin
from .models import ExerciseCategory, Exercise, ExerciseBlock, ExerciseType, Question


@admin.register(ExerciseBlock)
class ExerciseBlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order',)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('question_text', 'correct_answer', 'order')


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'block', 'difficulty', 'order', 'is_active')
    list_filter = ('block', 'difficulty', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exercise_type', 'question_text', 'correct_answer', 'order')
    list_filter = ('exercise_type__block',)
    search_fields = ('question_text',)


# Legacy models
@admin.register(ExerciseCategory)
class ExerciseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_active', 'created_at')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title',)

