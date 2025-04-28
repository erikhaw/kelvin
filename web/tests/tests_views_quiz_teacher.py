from django.test import TestCase
from django.urls import reverse

from tests_data.quiz.seed import tests_seed_quiz

class TeacherViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quiz,
         self.assigned_quiz, self.enrolled_quiz, self.enrolled_student, self.submitted_quiz) = tests_seed_quiz()

        login = self.client.login(username=self.teacher.username, password='teacher007')

        self.assertEqual(login, True)

    """
    Method that tests quiz scoring of non existent quiz
    """
    def test_quiz_scoring_non_existent(self):
        response = self.client.get(reverse('quiz_scoring', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quiz scoring of running quiz
    """
    def test_quiz_scoring_running_test(self):
        response = self.client.get(reverse('quiz_scoring', args=[self.enrolled_quiz.id]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quiz detail of non existent quiz
    """
    def test_quiz_detail_non_existent(self):
        response = self.client.get(reverse('quiz_detail', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quiz edit of non existent quiz
    """
    def test_quiz_edit_non_existent(self):
        response = self.client.get(reverse('quiz_edit', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quiz submits of non existent quiz
    """
    def test_quiz_submits_non_existent(self):
        response = self.client.get(reverse('quiz_submits', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests that correct templates are rendered for endpoints
    """
    def test_teacher_endpoints_render_template(self):
        test_cases = [
            {'url_name': 'quiz_list', 'args': [], 'expected_status': 200,
             'expected_template': 'web/quiz/quiz_list.html'},
            {'url_name': 'quiz_detail', 'args': [self.quiz.id], 'expected_status': 200,
             'expected_template': 'web/quiz/quiz.html'},
            {'url_name': 'quiz_edit', 'args': [self.quiz.id], 'expected_status': 200,
             'expected_template': 'web/quiz/quiz_edit.html'},
            {'url_name': 'quiz_scoring', 'args': [self.submitted_quiz.id], 'expected_status': 200,
             'expected_template': 'web/quiz/quiz.html'},
            {'url_name': 'quiz_submits', 'args': [self.quiz.id], 'expected_status': 200,
             'expected_template': 'web/quiz/quiz_submit_list.html'},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.get(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
                self.assertTemplateUsed(response, test_case['expected_template'])
