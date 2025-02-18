<script setup lang="ts">
/**
 * This component displays an editor that allows editing a quizz.
 * It is only available for teachers.
 */
import {ref, onMounted, onUnmounted, reactive, useTemplateRef, watch} from 'vue';
import {parse as yamlParse, stringify as yamlDump} from "yaml";
import {toast, updateGlobalOptions} from 'vue3-toastify';
import draggable from 'vuedraggable';
import hljs from 'highlight.js'
import 'vue3-toastify/dist/index.css';
import Modal from 'bootstrap/js/dist/modal';
import {getDataWithCSRF, getFromAPI} from '../utilities/api';
import QuizzAssign from "./QuizzAssign.vue";
import Editor from "../components/Editor.vue";
import {type EditorExtension} from '../utilities/EditorUtils';

type Question = {
  type: QuestionType;
  points: number;
  name: string;
  content: string;
  answers?: Answer[];
}

type Answer = {
  answer_content: string;
  is_correct: boolean;
  positive?: number;
  negative?: number;
}

type QuestionType = 'open' | 'abcd' | 'abcd.multiple';

type DraggableQuestion = {
  question: Question;
  hiddenId: number;
}

type QuizzUpdate = {
  shuffle: boolean;
  questions: Question[];
  quizz_directory: string;
}

const {id, quizz_directory, assignments, teacher, deletable} = defineProps<{
  id: number;
  assignments: string;
  quizz_directory: string;
  teacher: string;
  deletable: string;
}>();

updateGlobalOptions({
  multiple: false,
  theme: "auto",
  autoClose: 2000,
  transition: "slide",
  dangerouslyHTMLString: true
});

let changesMade = ref<boolean>(false);
const questionsRef = ref<DraggableQuestion[]>([]);
const hiddenIdRef = ref<number>(0);
const selectedHiddenIdRef = ref<number>(0);
const previewHtmlRef = ref<string>('');
const currentQuestionYamlRef = ref<string>('');
const previewBlockContentRef = useTemplateRef('previewBlockContent');
const quizzDirectoryRef = useTemplateRef('quizzDirectory');
const previewButtonRef = useTemplateRef('previewButton');
const shuffleRef = useTemplateRef('shuffle');
const isDeletableRef = ref<boolean>(deletable !== 'False');
const questionAddModalState = reactive({
  question_add_modal: null,
});

/**
 * Extension for the editor to provide hints and linting
 *
 * Hint is activated by using combination of ctrl + space
 *
 * @param filename Name of the file
 * @param content Content of the file
 * @param editor Editor instance
 * @param type Type of phase
 */
const extension = ((_, content, editor, type) => {
  if (type === 'setup') {
    return {
      spellCheck: true,
      gutters: ['CodeMirror-lint-markers']
    };
  } else if (type === 'hint') {
    const hints = ['name', 'points', 'type', 'content', 'answers', 'answer_content', 'is_correct', 'positive', 'negative'];

    const cursor = editor.getCursor();
    const token = editor.getTokenAt(cursor);

    const lowerCase = token.string.toLowerCase();

    const selected = hints.filter((hint) => hint.startsWith(lowerCase));

    return {
      hint: {
        list: selected,
        from: {
          line: cursor.line,
          ch: token.start
        },
        to: {
          line: cursor.line,
          ch: token.end
        }
      }
    };
  } else if (type === 'lint') {
    const parsed = yamlParse(content);
    const {isValid, errors} = validateQuestion(parsed);

    const cursor = editor.getCursor();

    if (!isValid) {
      return {
        lint: [{
          severity: "error",
          message: errors[0],
          from: {
            line: cursor.line,
            ch: 0
          },
          to: {
            line: cursor.line,
            ch: 0
          }
        }]
      }
    }
  }
}) satisfies EditorExtension;

/**
 * Get quizz from the server
 * @param id Quizz ID
 */
const getQuizz = async (id: number) => {
  const data = await getFromAPI<{yaml: string}>('/api/quizz/' + id);

  if (data && data.yaml) {
    const quizz = yamlParse(data.yaml);
    if (quizz.questions) {
      questionsRef.value = quizz.questions.map((question: any) => {
        return {
          question: question,
          hiddenId: hiddenIdRef.value++
        };
      });

      await updateCurrentQuestionYaml();
    }

    if (quizz.shuffle) {
      shuffleRef.value.checked = true;
    }
  }
};

/**
 * Update the current question YAML that is being edited
 */
const updateCurrentQuestionYaml = async () => {
  const index = await getIndexOfQuestionByHiddenId(selectedHiddenIdRef.value);

  currentQuestionYamlRef.value = index != -1 ? yamlDump(questionsRef.value[index].question) : '';
};

/**
 * Get the index of a question by its hidden id
 * @param hiddenId Hidden id of the question
 */
const getIndexOfQuestionByHiddenId = async (hiddenId: number): Promise<number> => {
  return questionsRef.value.findIndex((question) => question.hiddenId === hiddenId);
};

/**
 * Send quizz to the server in order to save it
 * @param quizzUpdate Quizz object
 */
const saveQuizzAPI = async (quizzUpdate: QuizzUpdate) => {
  const data = await getDataWithCSRF<{yaml: string}>('/api/quizz/' + id, 'POST', JSON.stringify(quizzUpdate));

  if (data && data.yaml) {
    hiddenIdRef.value = 0;

    const quizz = yamlParse(data.yaml);

    if (quizz.questions) {
      questionsRef.value = quizz.questions.map((question: any) => {
        return {
          question: question,
          hiddenId: hiddenIdRef.value++
        };
      });

      await selectQuestion(0);
    }
  }
};

/**
 * Checks if quizz is valid and then saves it
 */
const saveQuizz = async () => {
  const questions = questionsRef.value.map((question) => question.question);

  if (questions.every((question) => validateQuestion(question).isValid)) {
    const quizzUpdate = {
      questions: questions,
      quizz_directory: quizzDirectoryRef.value.value,
      shuffle: shuffleRef.value.checked
    };

    await saveQuizzAPI(quizzUpdate);

    changesMade.value = false;

    toast.success('Quizz saved.');
  } else {
    toast.error('Some questions are invalid.');
  }
};

/**
 * Select a question by its hidden id
 * @param hiddenId Hidden id of the question
 */
const selectQuestion = async (hiddenId: number) => {
  if (!questionsRef.value.some((question) => question.hiddenId === hiddenId)) {
    return;
  }

  selectedHiddenIdRef.value = hiddenId;

  await updateCurrentQuestionYaml();
  await previewQuestion();
};

/**
 * Show the preview of scoped question
 */
const previewQuestion = async () => {
  const index = await getIndexOfQuestionByHiddenId(selectedHiddenIdRef.value);

  if (index == -1) {
    return;
  }

  const {question} = questionsRef.value[index];

  if (previewBlockContentRef.value.getAttribute('data-index') == selectedHiddenIdRef.value.toString()) {
    return;
  }

  previewBlockContentRef.value.setAttribute('data-index', selectedHiddenIdRef.value.toString());

  previewBlockContentRef.value.style.opacity = '0';
  previewBlockContentRef.value.style.visibility = 'hidden';

  const {html} = await getDataWithCSRF<{
    html: string
  }>('/api/quizz/' + id + '/question/preview', 'POST',
      question.content);

  let answerHtml = '';

  if (question.type === 'abcd.multiple') {
    answerHtml = '<h6 class="mt-2"><strong>Answers:</strong></h6>';
  } else {
    answerHtml = '<h6 class="mt-2"><strong>Answer:</strong></h6>';
  }

  if (question.type == "open") {
    answerHtml += '<textarea class="form-control" rows="3"></textarea>';
  } else if (question.type == "abcd" || question.type == "abcd.multiple") {
    let answerNum = 1;
    const type = question.type == "abcd" ? "radio" : "checkbox";
    for (const answer of question.answers) {
      const res = await getDataWithCSRF<{
        html: string
      }>('/api/quizz/' + id + '/question/preview', 'POST',
          answer.answer_content);
      if (res.html != null) {
        answerHtml += `<div class="row border rounded mt-1 p-2">
                            <div class="col-1">
                                <strong>${answerNum++}.</strong>
                            </div>
                            <div class="col-10 d-flex justify-content-center">${res.html}</div>
                            <div class="col-1 align-self-center">
                                <input class="form-check-input" type="${type}" name="answer-preview">
                            </div>
                        </div>
                        `;
      }
    }
  } else {
    toast.error('Unknown question type');
    return;
  }

  const questionHtmlEl = document.createElement('div');

  questionHtmlEl.innerHTML = html + answerHtml;

  questionHtmlEl.querySelectorAll('code[class^=language]').forEach((target) => {
    hljs.highlightElement(target as HTMLElement);
  });

  previewHtmlRef.value = '<h6 class="mt-2"><strong>Question:</strong></h6>' + questionHtmlEl.innerHTML;

  previewBlockContentRef.value.style.visibility = 'visible';
  previewBlockContentRef.value.style.opacity = '1';
};

/**
 * Add a question to the quizz by its type
 * @param type Type of the question
 */
const addQuestion = async (type: QuestionType) => {
  const newDraggableQuestion = {hiddenId: hiddenIdRef.value++, question: {} as Question};

  if (type == "open") {
    newDraggableQuestion.question = {
      type: type,
      points: 2,
      name: "Question " + (questionsRef.value.length + 1),
      content: "What is output of this line of code?\n\n```c\nprintf(\"Hello world\");\n```",
    };
  } else if (type == "abcd") {
    newDraggableQuestion.question = {
      points: 3,
      type: type,
      name: "Question " + (questionsRef.value.length + 1),
      content: "Which C codes are syntactically wrong? Choose **one correct** answer.",
      answers: [
        {
          answer_content: "```c\n" +
              "        int main() {\n" +
              "            printf(\"Hello World\\n\")\n" +
              "            return 0;\n" +
              "        }\n" +
              "```", is_correct: false
        },
        {
          answer_content: "```c\n" +
              "      int main() {\n" +
              "        printf('Hello World\\n');\n" +
              "        return 0;\n" +
              "      }\n" +
              "```", is_correct: false
        },
        {
          answer_content: "```c\n" +
              "      int main() {\n" +
              "        printf(\"Hello World\\n\");\n" +
              "        return 0;\n" +
              "\n" +
              "```", is_correct: false
        },
        {answer_content: "All source codes are syntactically wrong.", is_correct: true},
      ]
    };
  } else if (type == "abcd.multiple") {
    newDraggableQuestion.question = {
      points: 5,
      type: type,
      name: "Question " + (questionsRef.value.length + 1),
      content: "Which C codes are syntactically wrong? Choose **all correct** answers.",
      answers: [
        {
          answer_content: "```c\n" +
              "        int main() {\n" +
              "            printf(\"Hello World\\n\")\n" +
              "            return 0;\n" +
              "        }\n" +
              "```", is_correct: true, positive: 25, negative: 50
        },
        {
          answer_content: "```c\n" +
              "      int main() {\n" +
              "        printf('Hello World\\n');\n" +
              "        return 0;\n" +
              "      }\n" +
              "```", is_correct: true, positive: 25, negative: 50
        },
        {
          answer_content: "```c\n" +
              "      int main() {\n" +
              "        printf(\"Hello World\\n\");\n" +
              "        return 0;\n" +
              "\n" +
              "```", is_correct: true, positive: 25, negative: 50
        },
        {
          answer_content: "All source codes are syntactically correct.",
          is_correct: false,
          positive: 25,
          negative: 100
        },
      ]
    };
  }

  questionsRef.value.push(newDraggableQuestion);

  selectedHiddenIdRef.value = hiddenIdRef.value - 1;
  await updateCurrentQuestionYaml();
  await previewQuestion();
  closeQuestionAddModal();

  changesMade.value = true;
};

/**
 * Remove a question from the quizz by its hidden id
 * @param hiddenId Hidden id of the question
 */
const removeQuestion = async (hiddenId: number) => {
  if (confirm('Are you sure you want to delete this question?')) {
    const toRemove = await getIndexOfQuestionByHiddenId(hiddenId);

    if (toRemove == -1) {
      return;
    }

    questionsRef.value.splice(toRemove, 1);

    changesMade.value = true;

    if (questionsRef.value.length === 0) {
      return;
    }

    await selectQuestion(questionsRef.value.find((question) => question.hiddenId !== hiddenId).hiddenId);

    await updateCurrentQuestionYaml();
  }
};

/**
 * Validate a question object
 * @param obj Question object
 */
const validateQuestion = (obj: any): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (typeof obj !== 'object' || obj === null) {
    errors.push('[type] must be a string of (open, abcd, abcd.multiple).');
    return {isValid: false, errors};
  }

  if (typeof obj.type !== 'string') errors.push('[type] must be a string of (open, abcd, abcd.multiple).');
  if (obj.type !== 'open' && obj.type !== 'abcd' && obj.type !== 'abcd.multiple') {
    errors.push('[type] must be a string of (open, abcd, abcd.multiple).');
  }
  if (typeof obj.points !== 'number') errors.push('[points] must be a number or is missing.');
  if (typeof obj.name !== 'string') errors.push('[name] must be a string or is missing.');
  if (typeof obj.content !== 'string') errors.push('[content] must be a string or is missing.');
  if (obj.answers && !Array.isArray(obj.answers)) {
    errors.push('[answers] must be an array.');
  } else if (obj.answers) {
    obj.answers.forEach((answer: any, index: number) => {
      if (typeof answer.answer_content !== 'string') {
        errors.push(`[answers[${index}].answer_content] must be a string or is missing.`);
      }
      if (typeof answer.is_correct !== 'boolean') {
        errors.push(`[answers[${index}].is_correct] must be a boolean or is missing.`);
      }
      if (
          (typeof answer.positive !== 'number' || typeof answer.negative !== 'number') && obj.type === 'abcd.multiple'
      ) {
        errors.push(
            `[answers[${index}]] must have both [positive] and [negative] fields as numbers.`
        );
      }
    });
  }
  else if(obj.type !== 'open') {
    errors.push('Types of (abcd, abcd.multiple) require [answers] field.');
  }

  return {isValid: errors.length === 0, errors};
}

/**
 * Update question object from currently edited YAML content
 */
const updateQuestionFromYaml = async (): Promise<boolean> => {
  try {
    const parsed = yamlParse(currentQuestionYamlRef.value);
    const {isValid, errors} = validateQuestion(parsed);

    if (isValid) {
      previewButtonRef.value.setAttribute('data-bs-toggle', 'tab');
      const index = await getIndexOfQuestionByHiddenId(selectedHiddenIdRef.value);
      if (index != -1) {
        if (yamlDump(questionsRef.value[index].question) !== currentQuestionYamlRef.value) {
          changesMade.value = true;
        }

        questionsRef.value[index].question = parsed;
        previewBlockContentRef.value.removeAttribute('data-index');
      } else {
        return false;
      }

      return true;
    }
  } catch (e) {
    console.error('Invalid YAML:', e);
  }

  previewHtmlRef.value = '';
  previewButtonRef.value.removeAttribute('data-bs-toggle');

  return false;
};

/**
 * Duplicate a quizz by its ID
 * @param id Quizz ID
 */
const duplicateQuizz = async (id: number) => {
  const data = await getDataWithCSRF<{id: number}>(`/api/quizz/${id}/duplicate`, 'POST', {
    quizz_id: id
  });

  if (data && data.id) {
    window.location.href = `/teacher/quizz/${data.id}/edit`;
  }
};

/**
 * Delete a quizz by its ID
 * @param id
 */
const deleteQuizz = async (id: number) => {
  if (confirm('Are you sure you want to delete this quizz?')) {
    const data = await getDataWithCSRF<{redirect: string}>(`/api/quizz/${id}`, 'DELETE');

    if (data && data.redirect) {
      window.removeEventListener('beforeunload', beforeWindowUnload);
      window.location.href = data.redirect;
    }
  }
};

/**
 * Open the question add modal
 */
const openQuestionAddModal = () => {
  questionAddModalState.question_add_modal.show()
}

/**
 * Close the question add modal
 */
const closeQuestionAddModal = () => {
  questionAddModalState.question_add_modal.hide()
}

/**
 * Checking possible unsaved changes
 * @param e BeforeUnloadEvent
 */
const beforeWindowUnload = (e: BeforeUnloadEvent) => {
  if (changesMade.value) {
    e.preventDefault();
  }
};

onMounted(async () => {
  await getQuizz(id);
  quizzDirectoryRef.value.value = quizz_directory;
  questionAddModalState.question_add_modal = new Modal('#question_add_modal', {})
  window.addEventListener('beforeunload', beforeWindowUnload);
  changesMade.value = false;
});

watch(currentQuestionYamlRef, () => {
  updateQuestionFromYaml();
});

onUnmounted(() => {
  window.removeEventListener('beforeunload', beforeWindowUnload);
});
</script>

<template>
  <div class="container">
    <div class="col-12 mb-2">
      <QuizzAssign :quizz_id="id" :assignments="assignments" :teacher="teacher" v-model="isDeletableRef"></QuizzAssign>
    </div>
    <div class="col-12">
      <button @click="openQuestionAddModal" class="btn btn-primary">Add question</button>
      <button :disabled="!changesMade || !questionsRef.length" @click="saveQuizz" class="btn btn-success ms-2">Save quizz</button>
    </div>
    <div class="input-group mt-2">
      <input id="quizz_directory" ref="quizzDirectory" type="text" class="form-control"
             @change="() => { changesMade = true; }">
      <a class="btn btn-outline-info" title="Show submits" :href="`/teacher/quizz/${id}/submits`">
              <span class="iconify" data-icon="ant-design:form-outlined"></span>
      </a>
      <button class="btn btn-outline-info" title="Duplicate this quizz" @click="duplicateQuizz(id)">
              <span class="iconify" data-icon="ant-design:copy-outlined"></span>
      </button>
      <a class="btn btn-outline-info" v-if="questionsRef.length" :href="`/teacher/quizz/${id}`" title="Display quizz">
                <span class="iconify" data-icon="bx:bx-link-external"></span>
      </a>
      <button class="btn btn-outline-danger" title="Delete quizz" @click="deleteQuizz(id)" :disabled="!isDeletableRef">
        <span class="iconify" data-icon="akar-icons:trash-can"></span>
      </button>
    </div>
    <div class="row mt-2">
      <div class="col-lg-3 col-12">
        <div class="d-flex align-items-center mb-3 col-12" v-if="questionsRef.length">
          <label for="shuffle" class="me-2">Shuffle questions:</label>
          <input class="form-check" ref="shuffle" type="checkbox" id="shuffle" @change="() => { changesMade = true; }">
        </div>
        <draggable
            :list="questionsRef"
            item-key="name"
            class="list-group mt-2"
            ghost-class="ghost"
            @change="() => { changesMade = true; }"
        >
          <template #item="{ element }">
            <div class="list-group-item p-1" @click="selectQuestion(element.hiddenId)">
              <div class="row">
                <div class="col-11 mt-2">
                  {{ element.question.name }}
                </div>
                <div class="col-1">
                  <button
                      @click="removeQuestion(element.hiddenId)"
                      class="btn btn-outline-danger float-end"
                      title="Smazat otázku"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </template>
        </draggable>
      </div>
      <div class="col-lg-9 col-12" v-if="questionsRef.length">
        <ul class="nav nav-tabs" id="quizzEditHeader" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" id="content-tab" data-bs-toggle="tab"
                    data-bs-target="#content-block"
                    type="button"
                    role="tab" aria-controls="content-block" aria-selected="true">Question content
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button @click="previewQuestion" ref="previewButton" class="nav-link" id="preview-tab" data-bs-toggle="tab"
                    data-bs-target="#preview-block" type="button" role="tab"
                    aria-controls="preview-block" aria-selected="false">Preview
            </button>
          </li>
        </ul>
        <div class="tab-content" id="quizzEditContent">
          <div class="tab-pane fade show active p-3" id="content-block" role="tabpanel" aria-labelledby="content-tab">
            <div class="col-12">
              <Editor
                  filename="quizz.yaml"
                  v-model:value="currentQuestionYamlRef"
                  @input="updateQuestionFromYaml"
                  :extensions="[extension]"
                  :lint="true"
                  :wrap="true"
              >
              </Editor>
            </div>
          </div>
          <div class="tab-pane fade p-3" id="preview-block" role="tabpanel" aria-labelledby="preview-tab">
            <div class="col-12">
              <div id="preview-block-content" ref="previewBlockContent" v-html="previewHtmlRef"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="modal fade" id="question_add_modal" tabindex="-1" aria-labelledby="question_add_modal_label"
       aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="question_add_modal_label">Add question</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="closeQuestionAddModal"></button>
        </div>
        <div class="modal-body d-flex justify-content-center">
          <button type="button" class="btn btn-primary" @click="addQuestion('open')">OPEN</button>
          <button type="button" class="btn btn-primary ms-1" @click="addQuestion('abcd')">ABCD</button>
          <button type="button" class="btn btn-primary ms-1" @click="addQuestion('abcd.multiple')">ABCD.MULTIPLE
          </button>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeQuestionAddModal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:global(#preview-block-content) {
  display: block;
  transition: opacity .5s ease 0s;
}

#preview-block-content:deep(img) {
  position: relative;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.ghost {
  opacity: 0.5;
  background: #c8ebfb;
}
</style>
