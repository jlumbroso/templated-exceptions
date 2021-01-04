import jinja2
import pytest

import templated_exceptions

SAMPLE_EXCEPTION_MESSAGE_JINJA2_TEMPLATE = """
    Some message template that takes two elements:
    - {{ variable_a }}
    - {{ variable_b }}
    - {{ variable_c[0] }}
    """

SAMPLE_EXCEPTION_ADHOC_MESSAGE = "some non-templated msg"

SAMPLE_EXCEPTION_VARIABLE_NAMES = [
    "variable_a",
    "variable_b",
    "variable_c",
]

SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1 = {
    "variable_a": 1,
    "variable_b": 1,
    "variable_c": [1],
}

SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_FAILS_1 = {
    "variable_a": 1,
    "variable_b": 1,
    "variable_c": 1,  # wrong type
}


class TestJinja2TemplatedException:
    def test_constructor_noargs(self):
        templated_exceptions.Jinja2TemplatedException()

    def test_constructor_msg(self):
        templated_exceptions.Jinja2TemplatedException(SAMPLE_EXCEPTION_ADHOC_MESSAGE)

    def test_clsmethod_template_render(self):
        assert templated_exceptions.Jinja2TemplatedException._template_render(
            template=SAMPLE_EXCEPTION_MESSAGE_JINJA2_TEMPLATE,
            ignore_missing=False,
            **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1,
        ) == jinja2.Template(SAMPLE_EXCEPTION_MESSAGE_JINJA2_TEMPLATE).render(
            **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1,
        )

    def test_clsmethod_template_render_none(self):
        assert (
            templated_exceptions.Jinja2TemplatedException._template_render(
                template=None,
            )
            is None
        )


class SampleJinja2Exception(
    templated_exceptions.Jinja2TemplatedException, RuntimeError
):
    TEMPLATE = SAMPLE_EXCEPTION_MESSAGE_JINJA2_TEMPLATE


class TestSampleJinja2Exception:
    def test_raise_by_class(self):
        """Check a TemplatedException class can be raised without constructor."""

        with pytest.raises(SampleJinja2Exception) as exc_info:
            raise SampleJinja2Exception

        assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_JINJA2_TEMPLATE
