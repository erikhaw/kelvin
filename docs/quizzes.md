# Quizzes

Quiz is defined using a YAML format and currently supports three types of questions. Questions can be added and edited
through the UI editor. Here are examples of each question type:

- Open question
```yaml
type: open
points: 2
name: Question 1
content: Write a command that prints a **"Hello World"** in C.
```
- ABCD
```yaml
type: abcd
points: 3
name: Question 2
content: Which C codes are syntactically wrong? Choose **one correct** answer.
answers:
  - answer_content: |-
      ```c
              int main() {
                  printf("Hello World\n")
                  return 0;
              }
      ```
    is_correct: false
  - answer_content: |-
      ```c
            int main() {
              printf('Hello World\n');
              return 0;
            }
      ```
    is_correct: false
  - answer_content: |-
      ```c
            int main() {
              printf("Hello World\n");
              return 0;

      ```
    is_correct: false
  - answer_content: All source codes are syntactically wrong.
    is_correct: true
```
- ABCD with multiple answers
```yaml
type: abcd.multiple
points: 5
name: Question 3
content: Which C codes are syntactically wrong? Choose **all correct** answers.
answers:
  - answer_content: |-
      ```c
              int main() {
                  printf("Hello World\n")
                  return 0;
              }
      ```
    is_correct: true
    positive: 25
    negative: 50
  - answer_content: |-
      ```c
            int main() {
              printf('Hello World\n');
              return 0;
            }
      ```
    is_correct: true
    positive: 25
    negative: 50
  - answer_content: |-
      ```c
            int main() {
              printf("Hello World\n");
              return 0;

      ```
    is_correct: true
    positive: 25
    negative: 50
  - answer_content: All source codes are syntactically correct.
    is_correct: false
    positive: 25
    negative: 100
```


