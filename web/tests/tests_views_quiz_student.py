from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from tests_data.quiz.seed import tests_seed_quiz

class StudentViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quiz,
         self.assigned_quiz, self.enrolled_quiz, self.enrolled_student, self.submitted_quiz) = tests_seed_quiz()

        login = self.client.login(username=self.enrolled_student.username, password='student007')

        self.assertEqual(login, True)

    """
    Method that tests student can continue filling enrolled quiz
    """
    def test_quiz_enroll_continue_filling(self):
        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quiz/quiz.html')

    """
    Method that tests student enrolling quiz that hes class not assigned to
    """
    def test_quiz_enroll_enrolling_non_assigned_user(self):
        login = self.client.login(username=self.students[5].username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling submitted quiz
    """
    def test_quiz_enroll_enrolling_submitted(self):
        login = self.client.login(username=self.submitted_quiz.student.username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling new
    """
    def test_quiz_enroll_enrolling_new(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quiz/quiz.html')

    """
    Method that tests student enrolling after deadline
    """
    def test_quiz_enroll_enrolling_after_deadline(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        self.assigned_quiz.deadline = self.assigned_quiz.deadline - timedelta(days=1)
        self.assigned_quiz.save()

        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student enrolling before assigned
    """
    def test_quiz_enroll_enrolling_before_assigned(self):
        login = self.client.login(username=self.students[4].username, password='student007')

        self.assertEqual(login, True)

        self.assigned_quiz.assigned = self.assigned_quiz.assigned + timedelta(days=1)
        self.assigned_quiz.save()

        response = self.client.post(reverse('quiz_enroll', args=[self.assigned_quiz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student accessing quiz results of another student
    """
    def test_student_quiz_result_access_another_student(self):
        response = self.client.post(reverse('quiz_result', args=[self.submitted_quiz.id]))

        self.assertEqual(response.status_code, 302)

    """
    Method that tests student accessing own quiz results
    """
    def test_student_quiz_result_access_own_returns_200(self):
        login = self.client.login(username=self.submitted_quiz.student.username, password='student007')

        self.assertEqual(login, True)

        response = self.client.post(reverse('quiz_result', args=[self.submitted_quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/quiz/quiz.html')

    """
    Method that tests student accessing quiz results when they are hidden
    """
    def test_student_quiz_result_access_when_results_hidden(self):
        login = self.client.login(username=self.submitted_quiz.student.username, password='student007')

        self.assertEqual(login, True)

        self.submitted_quiz.assigned_quiz.publish_results = False
        self.submitted_quiz.assigned_quiz.save()

        response = self.client.post(reverse('quiz_result', args=[self.submitted_quiz.id]))
        self.assertEqual(response.status_code, 302)

    """
    Method that tests that endpoints are protected against students access
    """
    def test_teacher_endpoints_should_return_302(self):
        test_cases = [
            {'url_name': 'quiz_list', 'args': [], 'expected_status': 302},
            {'url_name': 'quiz_detail', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'quiz_edit', 'args': [self.quiz.id], 'expected_status': 302},
            {'url_name': 'quiz_scoring', 'args': [self.enrolled_quiz.id], 'expected_status': 302},
            {'url_name': 'quiz_submits', 'args': [self.quiz.id], 'expected_status': 302},
        ]

        for test_case in test_cases:
            with self.subTest(case=test_case):
                response = self.client.post(reverse(test_case['url_name'], args=test_case['args']))
                self.assertEqual(response.status_code, test_case['expected_status'])
