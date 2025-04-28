from django.test import TestCase
from django.urls import reverse

from quiz.models import EnrolledQuiz
from tests_data.quiz.seed import tests_seed_quiz

class StudentViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quiz,
         self.assigned_quiz, self.enrolled_quiz, self.enrolled_student, self.submitted_quiz) = tests_seed_quiz()

        login = self.client.login(username=self.enrolled_student.username, password='student007')

        self.assertEqual(login, True)


    """
    Method that tests student working on quiz and submitting it
    """
    def test_submit_quiz_results(self):
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
        response = self.client.post(reverse('api_quiz_results', args=[self.enrolled_quiz.id, 0]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        enrolled_quiz = EnrolledQuiz.objects.get(id=self.enrolled_quiz.id)

        self.assertEqual(enrolled_quiz.submit, submit)
        self.assertEqual(enrolled_quiz.submitted, False)

        """
        Change one answer and send final submit
        """

        submit['test_question_abcd_multiple'][0]['answer'] = True

        response = self.client.post(reverse('api_quiz_results', args=[self.enrolled_quiz.id, 1]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        enrolled_quiz = EnrolledQuiz.objects.get(id=self.enrolled_quiz.id)

        self.assertEqual(enrolled_quiz.submit, submit)
        self.assertEqual(enrolled_quiz.submitted, True)

        """
        Because all answers are correct, score should be equal to max_points of quiz - points of open question, which
        is not automatically scored.
        """

        quiz_dto = self.quiz.get_dto()

        self.assertEqual(enrolled_quiz.score(), sum(map(lambda q: q.points if q.type != 'open' else 0, quiz_dto.questions)))

        """
        After submit, student should not be able to change answers.
        """

        submit['test_question_abcd_multiple'][0]['answer'] = False

        response = self.client.post(reverse('api_quiz_results', args=[self.enrolled_quiz.id, 0]), submit,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)


    """
    Method that tests that endpoints are protected against students access
    """
    def test_endpoints_should_return_302(self):
        test_cases = [
            {'url_name': 'api_quiz_list', 'args': [], 'expected_status': 302},
            {'url_name': 'api_quiz_yaml', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'api_quiz_question_preview', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'api_quiz_scoring', 'args': [0], 'expected_status': 302},
            {'url_name': 'api_quiz_list_subject', 'args': [self.upr.abbr], 'expected_status': 302},
            {'url_name': 'api_quiz_submits_list', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'api_quiz_submits_list_class', 'args': [self.quiz.id, self.upr_class1.id],
             'expected_status': 302},
            {'url_name': 'api_quiz_classes', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'api_quiz_assignments', 'args': [self.quiz.id], 'expected_status': 302},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.post(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
