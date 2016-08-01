from enum import Enum


_select_template = '''
<div>
{name}: <select name="{var}" required>
<option value="" disabled selected></option>
{options}
</select>
</div>'''


class Choice:
    def __init__(self, name, options):
        self.name = name
        self.var = name.replace(' ', '_').lower()
        self.options = Enum(
            self.var.capitalize() + 'Options',
            tuple(o['name'] for o in options))
        self._option_descriptions = {
            self.options[o['name']]: o['description'] for o in options}

    def validate(self, response):
        return self.options[response]

    @property
    def form_element(self):
        # FIXME: use proper templating
        return _select_template.format(
            name=self.name, var=self.var, options=''.join(
                '<option value="{val}">{desc}</option>'.format(
                    val=o.name, desc=self._option_descriptions[o]) for o in
                    self.options))


_form_template = '''
<form method="post">
{question_elements}
<button type="submit">Submit</button>
</form>'''


class Metric:
    def __init__(self, questions):
        self.questions = tuple(questions)

    @property
    def form_elements(self):
        return _form_template.format(
            question_elements='\n'.join(
                q.form_element for q in self.questions))

    def validate(self, response):
        validator_map = {q.var: q.validate for q in self.questions}
        validated = {}
        for k, v in response.items():
            validated[k] = validator_map.pop(k)(v)
        if validator_map:
            raise KeyError('Not all questions answered')
        return validated


def from_description(question_defs):
    return Metric(Choice(**qd) for qd in question_defs)
