from django.http import HttpResponseRedirect
from django.urls import reverse, resolve, Resolver404
from enum import Enum
from quizz.models import EnrolledQuizz

class ResultType(Enum):
    INTERMEDIATE = 0
    SUBMIT = 1

"""
Middleware to force redirect to quizz enroll page if student quizz is active and preventing to access urls that are not
allowed to visit during filling the quizz.
"""
class QuizzEnrollRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            enrolled_quizz = EnrolledQuizz.objects.get(student=request.user.id, submitted=False)

            enroll_url = reverse('quizz_enroll', args=[enrolled_quizz.assigned_quizz.id])

            allowed_urls = [
                enroll_url,
                reverse('api_quizz_results', args=[enrolled_quizz.id, ResultType.INTERMEDIATE.value]),
                reverse('api_quizz_results', args=[enrolled_quizz.id, ResultType.SUBMIT.value]),
                reverse('cas_ng_logout'),
            ]

            try:
                if resolve(request.path_info).url_name == 'quizz_asset':
                    allowed_urls.append(request.path_info)
            except Resolver404:
                pass

            if request.path_info not in allowed_urls:
                return HttpResponseRedirect(enroll_url)
        except EnrolledQuizz.DoesNotExist:
            pass

        response = self.get_response(request)

        return response
