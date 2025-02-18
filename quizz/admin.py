from django.contrib import admin
from quizz.models import Quizz, AssignedQuizz, EnrolledQuizz, TemplateQuizz

admin.site.register(Quizz)
admin.site.register(AssignedQuizz)
admin.site.register(EnrolledQuizz)
admin.site.register(TemplateQuizz)
