import json

from django.test import TestCase
from django.urls import reverse

from quizz.models import Quizz, EnrolledQuizz, AssignedQuizz
from tests_data.quizz.seed import tests_seed_quizz

class TeacherViews(TestCase):
    def setUp(self):
        (self.teacher, self.students, self.upr, self.upr_class1, self.upr_class2, self.quizz,
         self.assigned_quizz, self.enrolled_quizz, self.enrolled_student, self.submitted_quizz) = tests_seed_quizz()

        login = self.client.login(username=self.teacher.username, password='teacher007')

        self.assertEqual(login, True)


    """
    Method that tests quizz listing
    """
    def test_quizz_list(self):
        response = self.client.post(reverse('api_quizz_list'))

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content)

        self.assertEqual(content['count'], 1)
        self.assertEqual(content['quizzes'][0]['id'], self.quizz.id)

        Quizz.objects.get(pk=self.quizz.id).delete()

        response = self.client.post(reverse('api_quizz_list'))

        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['count'], 0)


    """
    Method that tests teacher scoring of submitted quizz
    """
    def test_quizz_scoring(self):
        """
        Quizz was submitted and scored automatically, so check if assigned points are correct
        """

        quizz_dto = self.quizz.get_dto()

        self.assertEqual(self.submitted_quizz.score(),
                         sum(map(lambda q: q.points if q.type != 'open' else 0, quizz_dto.questions)))

        """
        Teacher started scoring open question and decides to give student one bonus point for it
        """

        scoring = self.submitted_quizz.scoring

        scoring['test_question_open'] = {
            'points': 4,
            'comment': ''
        }

        response = self.client.post(reverse('api_quizz_scoring', args=[self.submitted_quizz.id]), scoring,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        """
        Points should be at maximum with one bonus point
        """

        submitted_quizz = EnrolledQuizz.objects.get(pk=self.submitted_quizz.id)

        self.assertEqual(submitted_quizz.score(), submitted_quizz.max_points + 1)


    """
    Method that tests submits listing
    """
    def test_quizz_submits_list(self):
        response = self.client.get(reverse('api_quizz_submits_list', args=[self.quizz.id]))

        self.assertEqual(response.status_code, 200)

        """
        There is one submit, so check if it is the same as the one that was submitted
        """

        content = json.loads(response.content)

        self.assertEqual(content['count'], 1)
        self.assertEqual(content['submits'][0]['id'], self.submitted_quizz.id)
        self.assertEqual(content['submits'][0]['student'], self.submitted_quizz.student.username)


    """
    Method that tests classes are assigned to quizz correctly
    """
    def test_quizz_classes(self):
        response = self.client.get(reverse('api_quizz_classes', args=[self.quizz.id]))

        self.assertEqual(response.status_code, 200)

        """
        Quizz is assigned to one class, so check if it is the same as the one that was assigned
        """

        content = json.loads(response.content)

        self.assertEqual(len(content["classes"]), 1)
        self.assertEqual(content["classes"][0]["classId"], self.upr_class1.id)

        """
        Let's assign the same quizz to another class and test if results are valid again
        """

        AssignedQuizz.objects.create(quizz=self.quizz, clazz=self.upr_class2, assigned=self.assigned_quizz.assigned, duration=60,
                                                      deadline=self.assigned_quizz.assigned, publish_results=True)

        response = self.client.get(reverse('api_quizz_classes', args=[self.quizz.id]))

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
    Method that tests assigning quizz to classes
    """
    def test_quizz_assignments(self):
        """
        There is one assignment, so check if it is the same as the one that was assigned
        """

        assignments_count = AssignedQuizz.objects.all().count()

        self.assertEqual(assignments_count, 1)

        assign = {
            "assignments": [
                {
                    "id": self.upr_class2.id,
                    "assigned": self.assigned_quizz.assigned.isoformat(),
                    "deadline": self.assigned_quizz.deadline.isoformat(),
                    "duration": 30,
                    "publish_results": True,
                },
            ],
        }

        """
        Now assign the same quizz to another class with different duration and check if results are valid
        """

        response = self.client.post(reverse('api_quizz_assignments', args=[self.quizz.id]), assign,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        assignments_count = AssignedQuizz.objects.all().count()

        self.assertEqual(assignments_count, 2)

        assignment = AssignedQuizz.objects.get(clazz=self.upr_class2, quizz=self.quizz)

        self.assertEqual(assignment.duration, 30)
