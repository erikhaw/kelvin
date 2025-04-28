import json

from django.test import TestCase
from django.urls import reverse

from quiz.models import Quiz, EnrolledQuiz, AssignedQuiz
from tests_data.quiz.seed import tests_seed_quiz

class TeacherViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quiz,
         self.assigned_quiz, self.enrolled_quiz, self.enrolled_student, self.submitted_quiz) = tests_seed_quiz()

        login = self.client.login(username=self.teacher.username, password='teacher007')

        self.assertEqual(login, True)


    """
    Method that tests quiz listing
    """
    def test_quiz_list(self):
        response = self.client.post(reverse('api_quiz_list'))

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        self.assertEqual(content['count'], 1)
        self.assertEqual(content['quizzes'][0]['id'], self.quiz.id)

        Quiz.objects.get(pk=self.quiz.id).delete()

        response = self.client.post(reverse('api_quiz_list'))

        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['count'], 0)


    """
    Method that tests teacher scoring of submitted quiz
    """
    def test_quiz_scoring(self):
        """
        Quiz was submitted and scored automatically, so check if assigned points are correct
        """

        quiz_dto = self.quiz.get_dto()

        self.assertEqual(self.submitted_quiz.score(),
                         sum(map(lambda q: q.points if q.type != 'open' else 0, quiz_dto.questions)))

        """
        Teacher started scoring open question and decides to give student one bonus point for it
        """

        scoring = self.submitted_quiz.scoring

        scoring['test_question_open'] = {
            'points': 4,
            'comment': ''
        }

        response = self.client.post(reverse('api_quiz_scoring', args=[self.submitted_quiz.id]), scoring,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        """
        Points should be at maximum with one bonus point
        """

        submitted_quiz = EnrolledQuiz.objects.get(pk=self.submitted_quiz.id)

        self.assertEqual(submitted_quiz.score(), submitted_quiz.max_points + 1)


    """
    Method that tests submits listing
    """
    def test_teacher_quiz_submit_exist_list(self):
        response = self.client.get(reverse('api_quiz_submits_list', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)

        """
        There is one submit, so check if it is the same as the one that was submitted
        """

        content = json.loads(response.content)

        self.assertEqual(content['count'], 1)
        self.assertEqual(content['submits'][0]['id'], self.submitted_quiz.id)
        self.assertEqual(content['submits'][0]['student'], self.submitted_quiz.student.username)


    """
    Method that tests classes are assigned to quiz correctly
    """
    def test_quiz_classes(self):
        response = self.client.get(reverse('api_quiz_classes', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)

        """
        Quiz is assigned to one class, so check if it is the same as the one that was assigned
        """

        content = json.loads(response.content)

        self.assertEqual(len(content["classes"]), 1)
        self.assertEqual(content["classes"][0]["classId"], self.upr_class1.id)

        """
        Let's assign the same quiz to another class and test if results are valid again
        """

        AssignedQuiz.objects.create(quiz=self.quiz, clazz=self.upr_class2, assigned=self.assigned_quiz.assigned, duration=60,
                                                      deadline=self.assigned_quiz.assigned, publish_results=True)

        response = self.client.get(reverse('api_quiz_classes', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        self.assertEqual(len(content["classes"]), 2)

        is_there_upr1 = False
        is_there_upr2 = False

        for clazz in content["classes"]:
            if clazz["classId"] == self.upr_class2.id:
                is_there_upr2 = True
            elif clazz["classId"] == self.upr_class1.id:
                is_there_upr1 = True

        self.assertTrue(is_there_upr1)
        self.assertTrue(is_there_upr2)


    """
    Method that tests assigning quiz to classes
    """
    def test_quiz_assignments(self):
        """
        There is one assignment, so check if it is the same as the one that was assigned
        """

        assignments_count = AssignedQuiz.objects.all().count()

        self.assertEqual(assignments_count, 1)

        assign = {
            "assignments": [
                {
                    "id": self.upr_class2.id,
                    "assigned": self.assigned_quiz.assigned.isoformat(),
                    "deadline": self.assigned_quiz.deadline.isoformat(),
                    "duration": 30,
                    "publish_results": True,
                },
            ],
        }

        """
        Now assign the same quiz to another class with different duration and check if results are valid
        """

        response = self.client.post(reverse('api_quiz_assignments', args=[self.quiz.id]), assign,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        assignments_count = AssignedQuiz.objects.all().count()

        self.assertEqual(assignments_count, 2)

        assignment = AssignedQuiz.objects.get(clazz=self.upr_class2, quiz=self.quiz)

        self.assertEqual(assignment.duration, 30)
