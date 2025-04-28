from django.http import HttpResponseRedirect
from django.urls import reverse, resolve, Resolver404
from enum import Enum
from quiz.models import EnrolledQuiz

class ResultType(Enum):
    INTERMEDIATE = 0
    SUBMIT = 1

"""
Middleware to force redirect to quiz enroll page if student quiz is active and preventing to access urls that are not
allowed to visit during filling the quiz.
"""
class QuizEnrollRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            enrolled_quiz = EnrolledQuiz.objects.get(student=request.user.id, submitted=False)

            enroll_url = reverse('quiz_enroll', args=[enrolled_quiz.assigned_quiz.id])

            allowed_urls = [
                enroll_url,
                reverse('api_quiz_results', args=[enrolled_quiz.id, ResultType.INTERMEDIATE.value]),
                reverse('api_quiz_results', args=[enrolled_quiz.id, ResultType.SUBMIT.value]),
                reverse('cas_ng_logout'),
            ]

            try:
                if resolve(request.path_info).url_name == 'quiz_asset':
                    allowed_urls.append(request.path_info)
            except Resolver404:
                pass

            if request.path_info not in allowed_urls:
                return HttpResponseRedirect(enroll_url)
        except EnrolledQuiz.DoesNotExist:
            pass

        response = self.get_response(request)

        return response
