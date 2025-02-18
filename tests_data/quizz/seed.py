import hashlib
import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from serde.json import to_json
from serde.yaml import to_yaml

from quizz.models import Quizz, AssignedQuizz, TemplateQuizz, EnrolledQuizz

from tests_data.common.seed import tests_seed_common

def tests_seed_quizz():
    (teacher, students, upr, upr_class1, upr_class2, semester) = tests_seed_common()

    quizz_data = {
        "questions": [
            {
                "content": 'What is output of this line of code?\n\n```c\nprintf("Hello world");\n```',
                "points": 3,
                "name": "Output of printf",
                "type": "open",
                "_id": "test_question_open",
            },
            {
                "content": "Which C codes are syntactically wrong? Choose **all correct** answers.",
                "points": 5,
                "name": "Source codes 1",
                "type": "abcd.multiple",
                "_id": "test_question_abcd_multiple",
                "answers": [
                    {
                        "answer_content": '```c\n        int main() {\n            printf("Hello World\\n")\n            return 0;\n        }\n```',
                        "is_correct": True,
                        "_id": "test_question_abcd_multiple_answer_1",
                        "positive": 25,
                        "negative": 50,
                    },
                    {
                        "answer_content": "```c\n      int main() {\n        printf('Hello World\\n');\n        return 0;\n      }\n```",
                        "is_correct": True,
                        "_id": "test_question_abcd_multiple_answer_2",
                        "positive": 25,
                        "negative": 50,
                    },
                    {
                        "answer_content": '```c\n      int main() {\n        printf("Hello World\\n");\n        return 0;\n\n```',
                        "is_correct": True,
                        "_id": "test_question_abcd_multiple_answer_3",
                        "positive": 25,
                        "negative": 50,
                    },
                    {
                        "answer_content": "All source codes are syntactically correct.",
                        "is_correct": False,
                        "_id": "test_question_abcd_multiple_answer_4",
                        "positive": 25,
                        "negative": 100,
                    },
                ],
            },
            {
                "content": "Which C codes are syntactically wrong? Choose **one correct** answer.",
                "points": 3,
                "name": "Source codes 2",
                "type": "abcd",
                "_id": "test_question_abcd",
                "answers": [
                    {
                        "answer_content": '```c\n        int main() {\n            printf("Hello World\\n")\n            return 0;\n        }\n```',
                        "is_correct": False,
                        "_id": "test_question_abcd_answer_1",
                    },
                    {
                        "answer_content": "```c\n      int main() {\n        printf('Hello World\\n');\n        return 0;\n      }\n```",
                        "is_correct": False,
                        "_id": "test_question_abcd_answer_2",
                    },
                    {
                        "answer_content": '```c\n      int main() {\n        printf("Hello World\\n");\n        return 0;\n\n```',
                        "is_correct": False,
                        "_id": "test_question_abcd_answer_3",
                    },
                    {
                        "answer_content": '```c\n      int main() {\n        printf("Hello World\\n);\n        return 0;\n\n```',
                        "is_correct": False,
                        "_id": "test_question_abcd_answer_4",
                    },
                    {
                        "answer_content": "All source codes are syntactically wrong.",
                        "is_correct": True,
                        "_id": "test_question_abcd_answer_5",
                    },
                ],
            },
        ]
    }

    quizz = Quizz.objects.create(title='Test Quizz', subject=upr, root='tests_data', src='quizz/quizzes/',
                                 semester=semester)

    quizz.write(to_yaml(quizz_data))

    now = timezone.now()

    tomorrow = now + timedelta(days=1)

    assigned_quizz = AssignedQuizz.objects.create(quizz=quizz, clazz=upr_class1, assigned=now, duration=60,
                                                  deadline=tomorrow, publish_results=True)

    enrolled_student = User.objects.create_user('enrolled_student', 'enrolled@testing.com', 'student007')
    submitted_student = User.objects.create_user('submitted_student', 'submitted@testing.com', 'student007')

    upr_class1.students.add(enrolled_student)
    upr_class1.students.add(submitted_student)

    quizz_dto = quizz.get_dto()

    quizz_json = to_json(quizz_dto).encode('utf-8')

    quizz_json_hash = hashlib.sha256(quizz_json).hexdigest()

    try:
        template = TemplateQuizz.objects.get(hash=quizz_json_hash)
    except TemplateQuizz.DoesNotExist:
        template = TemplateQuizz.objects.create(hash=quizz_json_hash, content=json.loads(quizz_json))
        template.save()

    enrolled_quizz = EnrolledQuizz.objects.create(assigned_quizz=assigned_quizz, template=template,
                                                  student=enrolled_student,
                                                  max_points=sum(map(lambda q: q.points, quizz_dto.questions)),
                                                  deadline=now + timedelta(minutes=assigned_quizz.duration))

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
            {'id': 'test_question_abcd_multiple_answer_1', 'answer': True},
            {'id': 'test_question_abcd_multiple_answer_2', 'answer': True},
            {'id': 'test_question_abcd_multiple_answer_3', 'answer': True},
            {'id': 'test_question_abcd_multiple_answer_4', 'answer': False},
        ],
    }

    submitted_quizz = EnrolledQuizz.objects.create(assigned_quizz=assigned_quizz, template=template,
                                                   student=submitted_student,
                                                   max_points=sum(map(lambda q: q.points, quizz_dto.questions)),
                                                   deadline=now + timedelta(minutes=assigned_quizz.duration),
                                                   submit=submit, submitted=True)
    submitted_quizz.score_questions()

    return (teacher, students, upr, upr_class1, upr_class2, quizz, assigned_quizz, enrolled_quizz, enrolled_student,
            submitted_quizz)
