from django.urls import path

from . import views
from common.inbus import views as inbus_views

urlpatterns = [
    path("tasks/<int:task_id>", views.task_detail),
    path("tasks/<int:task_id>/duplicate", views.duplicate_task),
    path("tasks/", views.task_detail),
    path("task-list", views.tasks_list_all),
    path("task-list/<subject_abbr>", views.tasks_list_all),
    path("submits/<int:task_assignment>", views.create_submit),
    path("info", views.info),
    path("classes", views.class_detail_list),
    path("classes/all", views.all_classes),
    path("classes/<int:class_id>/add_students", views.add_student_to_class),
    path("subject/<subject_abbr>", views.subject_list),
    path("subjects/all", views.subjects_all),
    path("teachers/all", views.teachers_all),
    path("reevaluate_task/<int:task_id>", views.reevaluate_task),
    path("search", views.search),
    path("transfer_students", views.transfer_students),
    path("semesters", views.semesters),
    path("import/activities", views.import_activities),
    path("inbus/subject_versions", inbus_views.subject_versions),
    path(
        "inbus/schedule/subject/version/<int:subject_version_id>",
        inbus_views.schedule_subject_by_version_id,
    ),
    path(
        "inbus/schedule/students/activity/<int:concrete_activity_id>",
        inbus_views.students_in_concrete_activity,
    ),
    path("quizz/<int:quizz_id>", views.quizz_yaml, name="api_quizz_yaml"),
    path("quizz/<int:quizz_id>/question/preview", views.quizz_question_preview, name="api_quizz_question_preview"),
    path("quizz/<int:enrolled_id>/result/<int:is_submit>", views.quizz_results, name="api_quizz_results"),
    path("quizz/<int:enrolled_id>/scoring", views.quizz_scoring, name="api_quizz_scoring"),
    path("quizz-list", views.quizzes_list_all, name="api_quizz_list"),
    path("quizz-list/<subject_abbr>", views.quizzes_list_all, name="api_quizz_list_subject"),
    path("quizz/<int:quizz_id>/submits", views.quizz_submits, name="api_quizz_submits_list"),
    path("quizz/<int:quizz_id>/submits/<class_id>", views.quizz_submits, name="api_quizz_submits_list_class"),
    path("quizz/<int:quizz_id>/classes", views.quizz_classes, name="api_quizz_classes"),
    path("quizz/add", views.quizz_add, name="api_quizz_add"),
    path("quizz/<int:quizz_id>/duplicate", views.quizz_duplicate),
    path("quizz/<int:quizz_id>/assignments", views.quizz_assignments, name="api_quizz_assignments"),
]
