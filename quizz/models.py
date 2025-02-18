import errno
import os
from shutil import copytree, rmtree

from django.db import models
from serde.yaml import from_yaml

from common.models import Class, Subject, User, Semester
from kelvin.settings import BASE_DIR
from quizz.dto import QuizzDto

"""
Model that represents a quizz.
"""
class Quizz(models.Model):
    title = models.CharField(max_length=100)
    # relative src path of quizz root directory
    src = models.CharField(max_length=255, verbose_name="Directory", unique=True)
    root = models.CharField(max_length=255, default="quizzes")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    """
    Method that writes content to the quizz file.
    """
    def write(self, yaml_content: str):
        with open(self.get_file_path(), 'w', encoding='utf-8') as file:
            file.write(yaml_content)

    """
    Method that reads content from the quizz file.
    """
    def read(self):
        with open(self.get_file_path(), 'r', encoding='utf-8') as file:
            return file.read()

    """
    Method that returns the directory path of the quizz.
    """
    def get_directory_path(self):
        return os.path.join(BASE_DIR, self.root, self.src)

    """
    Method that returns the file path of the quizz.
    """
    def get_file_path(self):
        return os.path.join(self.get_directory_path(), "quizz.yml")

    """
    Method that returns the identifier file path of the quizz.
    """
    def get_identifier_path(self):
        return os.path.join(self.get_directory_path(), ".quizz_id")

    """
    Method that returns a DTO of the quizz.
    """
    def get_dto(self):
        return from_yaml(QuizzDto, self.read())


    """
    Method that tries to set up the new directory for the quizz, returns True if successful, False if folder already
    exists, raise OSError otherwise.
    """
    def set_up_directory(self, new_src: str):
        if os.path.normpath(new_src) == os.path.normpath(self.src):
            return True

        try:
            copytree(os.path.join(BASE_DIR, self.root, self.src), os.path.join(BASE_DIR, self.root, new_src))

            old_src = self.src

            self.src = new_src

            self.save()

            rmtree(os.path.join(BASE_DIR, self.root, old_src))
        except OSError as e:
            if e.errno == errno.EEXIST:
                return False
            raise

        return True


"""
Model that represents an assigned quizz.
"""
class AssignedQuizz(models.Model):
    quizz = models.ForeignKey(Quizz, on_delete=models.CASCADE)
    clazz = models.ForeignKey(Class, on_delete=models.CASCADE)
    assigned = models.DateTimeField()
    duration = models.IntegerField() # in minutes
    deadline = models.DateTimeField()
    publish_results = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quizz.title} {self.clazz}"

    """
    Method that returns the maximum points of the assigned quizz.
    """
    def max_points(self):
        return sum(map(lambda q: q.points, self.quizz.get_dto().questions))


"""
Model that represents a template of enrolled quizz.
"""
class TemplateQuizz(models.Model):
    content = models.JSONField(default=dict)
    hash = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quizz template {self.id}"


"""
Model that represents an enrolled quizz.
"""
class EnrolledQuizz(models.Model):
    assigned_quizz = models.ForeignKey(AssignedQuizz, on_delete=models.CASCADE)
    template = models.ForeignKey(TemplateQuizz, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    deadline = models.DateTimeField()
    max_points = models.FloatField(default=0.0)
    submit = models.JSONField(default=dict)
    scoring = models.JSONField(default=dict)
    scored_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scored_by', null=True)
    submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    """
    Method that sums assigned scores of questions and returns the total score of the quizz.
    """
    def score(self):
        score = 0.0
        for key in self.scoring:
            score += float(self.scoring[key]['points'])
        return score

    def __str__(self):
        return f"{self.assigned_quizz.quizz.title} {self.student} {self.id}"


    """
    Method that computes the score of a submitted quizz for questions that are possible to score automatically.

    Automatically scored questions are of type: abcd, abcd.multiple 
    """
    def score_questions(self):
        template = self.template.content
        submit = self.submit
        scoring = {}
        questions = template.get('questions')

        if questions is not None:
            for question in questions:
                scoring[question['_id']] = {'points': 0.0, 'comment': ""}
                submit_answers = submit.get(question['_id'])
                if submit_answers is None:
                    continue
                if question['type'] == 'abcd':
                    for answer in question['answers']:
                        if answer['is_correct']:
                            for submit_answer in submit_answers:
                                if submit_answer['id'] == answer['_id'] and submit_answer['answer'] is True:
                                    scoring[question['_id']]['points'] = float(question['points'])
                elif question['type'] == 'abcd.multiple':
                    multiplier = 0
                    for answer in question['answers']:
                        for submit_answer in submit_answers:
                            if submit_answer['id'] == answer['_id']:
                                if submit_answer['answer'] == answer['is_correct']:
                                    multiplier += answer['positive']
                                else:
                                    multiplier -= answer['negative']
                    if multiplier < 0:
                        multiplier = 0
                    elif multiplier > 100:
                        multiplier = 100

                    scoring[question['_id']]['points'] = question['points'] * multiplier / 100

        self.scoring = scoring

        self.save()

"""
Function that returns a list of classes that are/can be assigned to the quizz.
"""
def quizz_assigned_classes(quizz: Quizz, requested_by: int):
    classes = Class.objects.current_semester().filter(subject=quizz.subject)
    user = User.objects.get(pk=requested_by)

    assignments_dtos = []

    for clazz in classes:
        assignment = AssignedQuizz.objects.filter(quizz=quizz.id, clazz=clazz.id)
        if assignment.count() == 0:
            assignments_dtos.append({'id': clazz.id, 'name': str(clazz), 'code': clazz.code,
                                 'teacher': clazz.teacher.username, 'timeslot': clazz.timeslot,
                                 'visible': clazz.teacher.id == user.id, 'deletable': True})
        elif assignment.count() == 1:
            assignment = assignment[0]
            deletable = assignment.enrolledquizz_set.count() == 0

            assignments_dtos.append({'id': clazz.id, 'name': str(clazz), 'assigned_id': assignment.id,
                                 'assigned': str(assignment.assigned), 'deadline': str(assignment.deadline),
                                 'duration': assignment.duration, 'code': clazz.code, 'timeslot': clazz.timeslot,
                                 'teacher': clazz.teacher.username, 'publish_results': assignment.publish_results,
                                 'visible': clazz.teacher.id == user.id, 'deletable': deletable})
        else:
            raise Exception("Multiple assignments for one class")

    assignments_dtos.sort(key=lambda x: (x['teacher'] != user.username, x['teacher'], 'assigned' not in x))

    return assignments_dtos
