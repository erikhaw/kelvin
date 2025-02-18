from django.test import TestCase
from django.urls import reverse

from tests_data.quizz.seed import tests_seed_quizz

class TeacherViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quizz,
         self.assigned_quizz, self.enrolled_quizz, self.enrolled_student, self.submitted_quizz) = tests_seed_quizz()

        login = self.client.login(username=self.teacher.username, password='teacher007')

        self.assertEqual(login, True)

    """
    Method that tests quizz scoring of non existent quizz
    """
    def test_quizz_scoring_non_existent(self):
        response = self.client.get(reverse('quizz_scoring', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quizz scoring of running quizz
    """
    def test_quizz_scoring_running_test(self):
        response = self.client.get(reverse('quizz_scoring', args=[self.enrolled_quizz.id]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quizz detail of non existent quizz
    """
    def test_quizz_detail_non_existent(self):
        response = self.client.get(reverse('quizz_detail', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quizz edit of non existent quizz
    """
    def test_quizz_edit_non_existent(self):
        response = self.client.get(reverse('quizz_edit', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests quizz submits of non existent quizz
    """
    def test_quizz_submits_non_existent(self):
        response = self.client.get(reverse('quizz_submits', args=[0]))

        self.assertEqual(response.status_code, 404)

    """
    Method that tests that correct templates are rendered for endpoints
    """
    def test_teacher_endpoints_render_template(self):
        test_cases = [
            {'url_name': 'quizz_list', 'args': [], 'expected_status': 200,
             'expected_template': 'web/quizz/quizz_list.html'},
            {'url_name': 'quizz_detail', 'args': [self.quizz.id], 'expected_status': 200,
             'expected_template': 'web/quizz/quizz.html'},
            {'url_name': 'quizz_edit', 'args': [self.quizz.id], 'expected_status': 200,
             'expected_template': 'web/quizz/quizz_edit.html'},
            {'url_name': 'quizz_scoring', 'args': [self.submitted_quizz.id], 'expected_status': 200,
             'expected_template': 'web/quizz/quizz.html'},
            {'url_name': 'quizz_submits', 'args': [self.quizz.id], 'expected_status': 200,
             'expected_template': 'web/quizz/quizz_submit_list.html'},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.get(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
                self.assertTemplateUsed(response, test_case['expected_template'])
