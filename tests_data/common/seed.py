from datetime import datetime, timezone
from django.contrib.auth.models import User, Group
from common.models import Subject, Class, Semester

def tests_seed_common():
    teacher = User.objects.create_user('teacher', 'teacher@testing.com', 'teacher007')

    teachers_group = Group.objects.get(name='teachers')
    teachers_group.user_set.add(teacher)

    students = list()

    for i in range(10):
        students.append(User.objects.create_user(f'student{i + 1}', f'student{i + 1}@testing.com', 'student007'))

    upr, _ = Subject.objects.get_or_create(
        name='Úvod do programování',
        abbr='UPR'
    )

    now = datetime.now(tz=timezone.utc)

    if 1 < now.month < 7:
        semester, _ = Semester.objects.get_or_create(
            begin=f'{now.year}-02-01',
            end=f'{now.year}-07-31',
            year=f'{now.year}',
            winter=False,
            active=True
        )
    else:
        semester, _ = Semester.objects.get_or_create(
            begin=f'{now.year}-10-01',
            end=f'{now.year + 1}-01-31',
            year=f'{now.year}',
            winter=True,
            active=True
        )

    upr_class1, _ = Class.objects.get_or_create(
        code='C/01',
        teacher=teacher,
        semester=semester,
        subject=upr,
        day="ST",
        time="7:15"
    )

    upr_class2, _ = Class.objects.get_or_create(
        code='C/02',
        teacher=teacher,
        semester=semester,
        subject=upr,
        day="ST",
        time="08:45"
    )

    for i in range(5):
        upr_class1.students.add(students[i])
        upr_class2.students.add(students[i + 5])

    return teacher, students, upr, upr_class1, upr_class2, semester
