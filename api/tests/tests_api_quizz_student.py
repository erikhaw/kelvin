from django.test import TestCase
from django.urls import reverse

from quizz.models import EnrolledQuizz
from tests_data.quizz.seed import tests_seed_quizz

class StudentViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quizz,
         self.assigned_quizz, self.enrolled_quizz, self.enrolled_student, self.submitted_quizz) = tests_seed_quizz()

        login = self.client.login(username=self.enrolled_student.username, password='student007')

        self.assertEqual(login, True)


    """
    Method that tests student working on quizz and submitting it
    """
    def test_submit_quizz_results(self):
        submit = {
            'test_question_open': [
                {'answer': 'Hello world'}
            ],
            'test_question_abcd': [
                {'id': 'test_question_abcd_answer_1', 'answer': False},
                {'id': 'test_question_abcd_answer_2', 'answer': False},
                {'id': 'test_question_abcd_answer_3', 'answer': False},
                {'id': 'test_question_abcd_answer_4', 'answer': False},
                {'id': 'test_question_abcd_answer_5', 'answer': True},
            ],
            'test_question_abcd_multiple': [
                {'id': 'test_question_abcd_multiple_answer_1', 'answer': False},
                {'id': 'test_question_abcd_multiple_answer_2', 'answer': True},
                {'id': 'test_question_abcd_multiple_answer_3', 'answer': True},
                {'id': 'test_question_abcd_multiple_answer_4', 'answer': False},
            ],
        }

        """
        Send intermediate results
        """
        response = self.client.post(reverse('api_quizz_results', args=[self.enrolled_quizz.id, 0]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        enrolled_quizz = EnrolledQuizz.objects.get(id=self.enrolled_quizz.id)

        self.assertEqual(enrolled_quizz.submit, submit)
        self.assertEqual(enrolled_quizz.submitted, False)

        """
        Change one answer and send final submit
        """

        submit['test_question_abcd_multiple'][0]['answer'] = True

        response = self.client.post(reverse('api_quizz_results', args=[self.enrolled_quizz.id, 1]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        enrolled_quizz = EnrolledQuizz.objects.get(id=self.enrolled_quizz.id)

        self.assertEqual(enrolled_quizz.submit, submit)
        self.assertEqual(enrolled_quizz.submitted, True)

        """
        Because all answers are correct, score should be equal to max_points of quizz - points of open question, which
        is not automatically scored.
        """

        quizz_dto = self.quizz.get_dto()

        self.assertEqual(enrolled_quizz.score(), sum(map(lambda q: q.points if q.type != 'open' else 0, quizz_dto.questions)))

        """
        After submit, student should not be able to change answers.
        """

        submit['test_question_abcd_multiple'][0]['answer'] = False

        response = self.client.post(reverse('api_quizz_results', args=[self.enrolled_quizz.id, 0]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)


    """
    Method that tests that endpoints are protected against students access
    """
    def test_endpoints_should_return_302(self):
        test_cases = [
            {'url_name': 'api_quizz_list', 'args': [], 'expected_status': 302},
            {'url_name': 'api_quizz_yaml', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'api_quizz_question_preview', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'api_quizz_scoring', 'args': [0], 'expected_status': 302},
            {'url_name': 'api_quizz_list_subject', 'args': [self.upr.abbr], 'expected_status': 302},
            {'url_name': 'api_quizz_submits_list', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'api_quizz_submits_list_class', 'args': [self.quizz.id, self.upr_class1.id],
             'expected_status': 302},
            {'url_name': 'api_quizz_classes', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'api_quizz_assignments', 'args': [self.quizz.id], 'expected_status': 302},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.post(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
