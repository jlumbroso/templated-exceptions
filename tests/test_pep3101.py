import collections
import random

import pytest

import templated_exceptions

SAMPLE_EXCEPTION_MESSAGE_TEMPLATE = """
    Some message template that takes two elements:
    - {variable_a}
    - {variable_b}
    - {variable_c[0]}
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


class TestPEP3101TemplatedException:
    def test_constructor_noargs(self):
        templated_exceptions.PEP3101TemplatedException()

    def test_constructor_msg(self):
        templated_exceptions.PEP3101TemplatedException("some msg")

    def test_clsmethod_template_render(self):
        assert templated_exceptions.PEP3101TemplatedException._template_render(
            template=SAMPLE_EXCEPTION_MESSAGE_TEMPLATE,
            ignore_missing=False,
            **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1,
        ) == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE.format(
            **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1,
        )

    def test_clsmethod_template_render_none(self):
        assert (
            templated_exceptions.PEP3101TemplatedException._template_render(
                template=None,
            )
            is None
        )

    def test_clsmethod_template_render_missing_keys_error(self):
        with pytest.raises(templated_exceptions.TemplatedExceptionInternalRuntimeError):
            templated_exceptions.PEP3101TemplatedException._template_render(
                template=SAMPLE_EXCEPTION_MESSAGE_TEMPLATE,
                ignore_missing=False,
            )

    def test_clsmethod_template_render_missing_keys_ignore(self):
        assert templated_exceptions.PEP3101TemplatedException._template_render(
            template=SAMPLE_EXCEPTION_MESSAGE_TEMPLATE,
            ignore_missing=True,
        ) == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE.format_map(
            collections.defaultdict(lambda: templated_exceptions._MISSING_KEY_STR),
        )

    def test_clsmethod_template_render_key_type_error(self):
        with pytest.raises(templated_exceptions.TemplatedExceptionInternalRuntimeError):
            templated_exceptions.PEP3101TemplatedException._template_render(
                template=SAMPLE_EXCEPTION_MESSAGE_TEMPLATE,
                ignore_missing=False,
                **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_FAILS_1,
            )


class SampleException(templated_exceptions.PEP3101TemplatedException, RuntimeError):
    TEMPLATE = SAMPLE_EXCEPTION_MESSAGE_TEMPLATE


class TestSampleException:
    def test_raise_by_class(self):
        """Check a TemplatedException class can be raised without constructor."""

        with pytest.raises(SampleException) as exc_info:
            raise SampleException

        assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE

    def test_init_no_args(self):
        """Check a TemplatedException class can be initialized without arguments."""

        exc = SampleException()

        assert exc.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE

    def test_raise_no_args(self):
        """Check a TemplatedException class can be raised without arguments."""

        with pytest.raises(SampleException) as exc_info:
            raise SampleException()

        assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE

    def test_init_adhoc_msg(self):
        """Check a TemplatedException class can be initialized with a static message."""

        exc = SampleException(SAMPLE_EXCEPTION_ADHOC_MESSAGE)

        assert exc.args[0] == SAMPLE_EXCEPTION_ADHOC_MESSAGE

    def test_raise_adhoc_msg(self):
        """Check a TemplatedException class can be raised with a static message."""

        with pytest.raises(SampleException) as exc_info:
            raise SampleException(SAMPLE_EXCEPTION_ADHOC_MESSAGE)

        assert exc_info.value.args[0] == SAMPLE_EXCEPTION_ADHOC_MESSAGE

    def test_raise_with_all_args(self):
        """
        Check a TemplatedException class can be raised with all template variables
        provided.
        """

        with pytest.raises(SampleException) as exc_info:
            raise SampleException(**SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1)

        assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE.format(
            **SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1
        )

    @pytest.mark.repeat(10)
    def test_raise_with_missing_args(self):
        """
        Check a TemplatedException class can be raised with all template variables
        provided.
        """

        example_assignment = SAMPLE_EXCEPTION_VARIABLE_ASSIGNMENTS_SUCCESS_1

        keep_or_drop_vars = {
            key: random.choice([True, False]) for key in example_assignment.keys()
        }

        template_vars = {
            key: value
            for (key, value) in example_assignment.items()
            if keep_or_drop_vars.get(key, False)
        }

        ref_template_vars = {
            key: (
                value
                if keep_or_drop_vars.get(key, False)
                else templated_exceptions._MISSING_KEY_STR
            )
            for (key, value) in example_assignment.items()
        }

        with pytest.raises(SampleException) as exc_info:
            raise SampleException(**template_vars)

        if len(template_vars) == 0:
            assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE
        else:
            assert exc_info.value.args[0] == SAMPLE_EXCEPTION_MESSAGE_TEMPLATE.format(
                **ref_template_vars
            )

    def test_varnames_with_args(self):

        # compute the varnames() from the exc
        exc = SampleException()
        exc_varnames_set = set(exc._varnames())

        # create reference set
        ref_varnames_set = set(SAMPLE_EXCEPTION_VARIABLE_NAMES)

        # compare
        assert exc_varnames_set == ref_varnames_set
