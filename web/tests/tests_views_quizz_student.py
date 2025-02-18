from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from tests_data.quizz.seed import tests_seed_quizz

class StudentViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quizz,
         self.assigned_quizz, self.enrolled_quizz, self.enrolled_student, self.submitted_quizz) = tests_seed_quizz()

        login = self.client.login(username=self.enrolled_student.username, password='student007')

        self.assertEqual(login, True)

    """
    Method that tests student can continue filling enrolled quizz
    """
    def test_quizz_enroll_continue_filling(self):
        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quizz/quizz.html')

    """
    Method that tests student enrolling quizz that hes class not assigned to
    """
    def test_quizz_enroll_enrolling_non_assigned_user(self):
        login = self.client.login(username=self.students[5].username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling submitted quizz
    """
    def test_quizz_enroll_enrolling_submitted(self):
        login = self.client.login(username=self.submitted_quizz.student.username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling new
    """
    def test_quizz_enroll_enrolling_new(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quizz/quizz.html')

    """
    Method that tests student enrolling after deadline
    """
    def test_quizz_enroll_enrolling_after_deadline(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        self.assigned_quizz.deadline = self.assigned_quizz.deadline - timedelta(days=1)
        self.assigned_quizz.save()

        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling before assigned
    """
    def test_quizz_enroll_enrolling_before_assigned(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        self.assigned_quizz.assigned = self.assigned_quizz.assigned + timedelta(days=1)
        self.assigned_quizz.save()

        response = self.client.post(reverse('quizz_enroll', args=[self.assigned_quizz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student accessing quizz results of another student
    """
    def test_student_quizz_result_access_another_student(self):
        response = self.client.post(reverse('quizz_result', args=[self.submitted_quizz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student accessing own quizz results
    """
    def test_student_quizz_result_access_own(self):
        login = self.client.login(username=self.submitted_quizz.student.username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quizz_result', args=[self.submitted_quizz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quizz/quizz.html')

    """
    Method that tests student accessing quizz results when they are hidden
    """
    def test_student_quizz_result_access_when_results_hidden(self):
        login = self.client.login(username=self.submitted_quizz.student.username, password='student007')

        self.assertEqual(login, True)

        self.submitted_quizz.assigned_quizz.publish_results = False
        self.submitted_quizz.assigned_quizz.save()

        response = self.client.post(reverse('quizz_result', args=[self.submitted_quizz.id]))
        self.assertEqual(response.status_code, 302)

    """
    Method that tests that endpoints are protected against students access
    """
    def test_teacher_endpoints_should_return_302(self):
        test_cases = [
            {'url_name': 'quizz_list', 'args': [], 'expected_status': 302},
            {'url_name': 'quizz_detail', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'quizz_edit', 'args': [self.quizz.id], 'expected_status': 302},
            {'url_name': 'quizz_scoring', 'args': [self.enrolled_quizz.id], 'expected_status': 302},
            {'url_name': 'quizz_submits', 'args': [self.quizz.id], 'expected_status': 302},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.post(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
