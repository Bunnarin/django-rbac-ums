// static/js/core/template_builder.js

class FormTemplateBuilder {
    constructor(config) {
        this.questionsContainer = document.getElementById(config.containerId);
        this.addQuestionBtn = document.getElementById(config.addBtnId);
        this.questionTemplate = document.getElementById(config.templateId);
        this.formElement = document.getElementById(config.formId);
        this.jsonInput = document.getElementById(config.jsonInputId);
        this.initialData = config.initialData || [];

        this.questionCounter = 0; // Use a distinct counter for unique IDs across sessions/loads

        this.initEventListeners();
        this.loadInitialData();
    }

    initEventListeners() {
        this.addQuestionBtn.addEventListener('click', () => this.addQuestion());
        this.formElement.addEventListener('submit', (event) => this.handleSubmit(event));
        
        this.questionsContainer.addEventListener('click', (event) => {
            const removeBtn = event.target.closest('.remove-question');
            if (removeBtn) {
                removeBtn.closest('.question-block').remove();
                this.updateQuestionNumbers();
            }
        });
        this.questionsContainer.addEventListener('change', (event) => {
            if (event.target.classList.contains('field-type')) {
                this.toggleTypeSpecificOptions(event.target.closest('.question-block'));
            }
        });
    }

    updateQuestionNumbers() {
        const questionBlocks = this.questionsContainer.querySelectorAll('.question-block');
        questionBlocks.forEach((block, index) => {
            block.querySelector('.question-number').textContent = index + 1;
            block.setAttribute('data-index', index);

            const isRequiredCheckbox = block.querySelector('.is-required');
            if (isRequiredCheckbox) {
                isRequiredCheckbox.id = `is_required_${index}`;
                const labelForRequired = block.querySelector(`label[for^="is_required_"]`);
                if (labelForRequired) {
                    labelForRequired.setAttribute('for', `is_required_${index}`);
                }
            }
        });
    }

    toggleTypeSpecificOptions(questionBlock) {
        const fieldType = questionBlock.querySelector('.field-type').value;
        const choicesGroup = questionBlock.querySelector('.choices-group');

        choicesGroup.style.display = 'none'; // Hide by default

        switch (fieldType) {
            case 'dropdown':
            case 'checkbox':
                choicesGroup.style.display = 'block';
                break;
        }
    }

    addQuestion(fieldDef = {}) {
        const clone = this.questionTemplate.content.cloneNode(true);
        const newQuestionBlock = clone.querySelector('.question-block');
        
        newQuestionBlock.setAttribute('data-internal-id', `q_${this.questionCounter++}`);
        
        if (Object.keys(fieldDef).length > 0) {
            newQuestionBlock.querySelector('.question-title').value = fieldDef.title || '';
            newQuestionBlock.querySelector('.field-type').value = fieldDef.type || 'text';
            newQuestionBlock.querySelector('.is-required').checked = fieldDef.is_required || false;

            if (fieldDef.choices !== undefined && Array.isArray(fieldDef.choices)) {
                newQuestionBlock.querySelector('.field-choices').value = fieldDef.choices.join('\n');
            }
        }

        this.questionsContainer.appendChild(clone);
        this.updateQuestionNumbers();
        this.toggleTypeSpecificOptions(newQuestionBlock);
    }

    loadInitialData() {
        if (this.initialData && this.initialData.length > 0) {
            this.initialData.forEach(fieldDef => this.addQuestion(fieldDef));
        }
    }

    collectTemplateJsonData() {
        const questionDefinitions = [];
        const questionBlocks = this.questionsContainer.querySelectorAll('.question-block');

        if (questionBlocks.length === 0) {
            alert('Please add at least one question to the template.');
            return null;
        }

        for (let i = 0; i < questionBlocks.length; i++) {
            const block = questionBlocks[i];

            const questionTitleInput = block.querySelector('.question-title');
            const questionTitle = questionTitleInput.value.trim();
            const fieldType = block.querySelector('.field-type').value;
            const isRequired = block.querySelector('.is-required').checked;

            if (!questionTitle) {
                alert(`Question ${i + 1}: Question Title cannot be empty.`);
                questionTitleInput.focus();
                return null;
            }

            let fieldDef = {
                label: questionTitle,
                type: fieldType,
                required: isRequired,
            };

            if (fieldType === 'dropdown' || fieldType === 'checkbox') {
                const choicesTextInput = block.querySelector('.field-choices');
                const choicesText = choicesTextInput.value.trim();

                if (!choicesText) {
                    alert(`Question ${i + 1}: Choices cannot be empty`);
                    choicesTextInput.focus();
                    return null;
                }

                fieldDef.choices = choicesText.split('\n').map(choice => choice.trim()).filter(choice => choice !== '');
            }
            questionDefinitions.push(fieldDef);
        }
        return questionDefinitions;
    }


    handleSubmit(event) {
        event.preventDefault(); // Prevent default form submission

        const templateData = this.collectTemplateJsonData();

        // Only proceed if templateData is not null (meaning no validation errors occurred)
        if (templateData !== null) {
            this.jsonInput.value = JSON.stringify(templateData);
            this.formElement.submit(); // Submit the form programmatically
        } else {
            // Validation failed, alerts already shown by collectTemplateJsonData
            // No further action needed here.
        }
    }
}