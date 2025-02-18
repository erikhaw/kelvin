from django.http import HttpResponse
from unidecode import unidecode

from web.markdown_utils import process_markdown


def file_response(file, filename: str, mimetype: str) -> HttpResponse:
    response = HttpResponse(file, mimetype)
    response["Content-Disposition"] = f'attachment; filename="{unidecode(filename)}"'
    return response


"""
Helper function that renders a markdown content of question and its answers to HTML and returns them.
"""
def quizz_to_html(quizz_directory: str, quizz: dict):
    result = []

    for question in quizz['questions']:
        question_render = {
            'id': question.get('_id'),
            'type': question['type'],
            'points': question['points'],
            'name': question['name'],
            'htmlContent': process_markdown(quizz_directory, question['content'], 'quizz').content
        }
        if question.get('answers'):
            answers = []
            for answer in question['answers']:
                answers.append({
                    'id': answer.get('_id'),
                    'htmlContent': process_markdown(quizz_directory, answer['answer_content'], 'quizz').content,
                })
            question_render['answers'] = answers
        result.append(question_render)

    return result
