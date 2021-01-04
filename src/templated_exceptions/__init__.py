"""
Package to introduce exceptions with templated messages.

This package makes it easy to define custom exceptions with
templated error messages, such that the exceptions only needs
to be raised with the differing parameters, rather than the
full error message. This provides excellent user description
of errors, as they can be explained once, and optimized for
clarity.
"""

import collections
import typing

_HAS_JINJA_2 = True

try:
    import jinja2
except ImportError:  # pragma: no cover
    jinja2 = None
    _HAS_JINJA_2 = False


__author__ = "Jérémie Lumbroso <lumbroso@cs.princeton.edu>"

__version__ = "20.1.0"

__all__ = [
    "TemplatedException",
    "PEP3101TemplatedException",
    "Jinja2TemplatedException",
]


_DEBUG = False
_TEMPLATE_FIELD_NAME = "TEMPLATE"
_MISSING_KEY_STR = "..."


class TemplatedExceptionInternalRuntimeError(RuntimeError):
    """
    Raised when an unsolvable issue occurs while rendering an exception's message.

    This exception is raised when the template of a templated exception's message
    cannot be rendered. Typically, these are problems that can be solved at compile
    time: For instance, such a problem might arise from a syntactically invalid
    template, or if not all template variables are provided when the exception is
    raised.
    """


# Standard (PEP 3101) templating engine


class PEP3101TemplatedException(Exception):
    """
    Implements exceptions with templated messages using PEP 3101 string formatting.

    The :py:exc:`TemplatedException` exception extends the standard Python
    generic :py:exc:`Exception` exception class, by allowing for templated
    messages. When raising a templated exception, only the parameters of
    the template need to be provided, and the final message will be formatted
    when the exception is raised.

    The template can be configured as a the :py:data:`TEMPLATE`
    class attribute, using Python's built-in advanced string formatting
    feature from PEP 3101. Another class, :py:exc:`Jinja2TemplatedException`
    provides support for the :py:mod:`jinja2` templating format.

    .. code-block::python
       :linenos:
       lineno-start: 1

       class NonEmptyListException(TemplatedException, RuntimeError):
           TEMPLATE = "The list you provided was not empty: {lst}."

       raise NonEmptyListException(lst=[1, 2, 3])


    To maintain compatibility with standard exceptions, every descendant of
    :py:exc:`TemplatedException` can also receive as constructor a single,
    unnamed parameter for the full message of the exception.

    .. code-block::python
       :linenos:
       lineno-start: 5

       raise NonEmptyListException("some msg without templating")

    If any problem occurs while rendering the template of a templated exception,
    the :py:exc:`TemplatedExceptionInternalRuntimeError` exception is raised.
    """

    # CLASS METHODS

    @classmethod
    def _template_render(
        cls, template: str, ignore_missing: bool = True, **kwargs
    ) -> typing.Optional[str]:
        """
        Render a template with provided keyword arguments, using class' template engine.

        :param template: The PEP 3101 template to use
        :param ignore_missing: Flag for whether to ignore missing template variables
        :param **kwargs: The dictionary to pass to the templating engine

        :return: The rendered template
        :raises TemplatedExceptionInternalRuntimeError: If there are any
            unresolved issues when rendering the template (such as a syntactically
            invalid template; or missing template variables)
        """

        # anticipate most likely error!
        if template is None:
            return

        try:
            if ignore_missing:
                new_dict = collections.defaultdict(lambda: _MISSING_KEY_STR)
                new_dict.update(**kwargs)
                kwargs = new_dict

            ret = template.format_map(kwargs)
            return ret

        except KeyError as exc:
            # missing keys in template
            raise TemplatedExceptionInternalRuntimeError(
                "missing key while rendering (PEP 3101) templated exception message",
            ) from exc

        except Exception as exc:
            # other problem
            raise TemplatedExceptionInternalRuntimeError(
                "unexpected error while rendering (PEP 3101) templated exception "
                "message",
            ) from exc

    @classmethod
    def _template(cls, **kwargs) -> typing.Optional[str]:
        """
        Get the class template, or silently fails if none exists.

        Optionally, if keyword arguments are provided, these will be used as
        template variables with which to render the template (using the class'
        :py:meth:`_render_template()` method). If no keyword arguments are
        provided, the template will be returned as it was defined.

        :param **kwargs: Optionally, keyword arguments containing the template
            variables

        :return: This templated exception's class template, if one is defined
        """

        try:
            template = getattr(cls, _TEMPLATE_FIELD_NAME)
        except AttributeError:
            # no template available
            return

        # determine if we can just return the unrendered template

        if template is None or kwargs is None or len(kwargs) == 0:
            return template

        # attempting to render, if kwargs are provided

        ret = cls._template_render(
            template=template,
            **kwargs,
        )

        return ret

    # noinspection PyBroadException
    @classmethod
    def _varnames(cls) -> typing.List[str]:
        """
        Get a list of the variables in this exception's template.

        :return: A list of all variable names for the templated exception's
            template, and an empty list if no template is defined
        """

        template = cls._template()

        varnames = []

        # to guess all the format parameters, we try to
        # render the formatted template and catch KeyError exceptions
        # as they occur (relies on the fact that the missing key name
        # is the args[0] of the KeyError exception)

        while True:
            kwargs = dict(zip(varnames, [""] * len(varnames)))
            try:
                template.format(**kwargs)

            except KeyError as key_error:
                # a key is missing, so we still have to check
                # if there other keys, hence new iteration
                missing = key_error.args[0]
                varnames.append(missing)
                continue

            except Exception:  # noqa: E722, S110
                # some unexpected error
                pass

            break

        return varnames

    # INSTANCE METHODS

    def __init__(self, *args, passthrough: bool = False, **kwargs):
        """
        Initialize templated exception, with template variables as keyword arguments.

        :param args: For backwards compatibility, allow unnamed arguments
        :param passthrough: Flag to pre-render the template, and pass it as a
            string to the base exception class
        :param kwargs: The template variables provided as keyword arguments
        """

        self._args = args
        self._kwargs = kwargs

        # Call the BaseException constructor with a pre-rendered
        # message

        if self._has_message():

            # a specific message is provided to the constructor
            # (base class cannot take kwargs)

            super().__init__(*args)

        elif passthrough:

            # no specific message: use rendered string + args
            # (this will be output using standard Python exception
            # output per RFC 352)

            super().__init__(
                self._template(**self._kwargs),
                *args,
            )

        else:

            # no specific message: use rendered string
            # do not make the args visible to the base class

            super().__init__(
                self._template(**self._kwargs),
            )

    def _has_message(self) -> bool:
        """
        Determine whether this exception was initialized with a message.

        :return: :py:data:`True` if the exception was initialized with
            a static message; :py:data:`False` otherwise
        """

        # in Python 3, the message of an exception is typically
        # stored in args[0]
        try:
            args = getattr(self, "_args", None)
            return not (args is None or len(args) == 0)
        except AttributeError:
            # there is no attribute called '_args'
            return False

    # noinspection PyBroadException
    def __str__(self) -> str:
        """
        Get a string message for the exception.

        :return: A string message for the exception
        """

        # this method is called when rendering an exception message
        # after an exception has been raised; if this method fails
        # it will confuse the error output for the developer/end-user
        #
        # => we must suppress any errors, *except* if debugging this
        # module

        rendered_template = None
        try:
            rendered_template = self._template(**self._kwargs)

        except Exception as exc:
            if _DEBUG:
                raise TemplatedExceptionInternalRuntimeError(
                    "unexpected error while rendering (PEP 3101) templated "
                    "while exception is being raised; DEBUG is turned on for "
                    "the templated-exceptions package to determine the root "
                    "cause of this issue",
                ) from exc

        if self._has_message() or rendered_template is None:
            return super().__str__()

        return rendered_template


# aliasing the name for convenience
TemplatedException = PEP3101TemplatedException


# Jinja2 templating engine


class Jinja2TemplatedException(TemplatedException):
    """
    Implements exceptions with templated messages using Jinja2 string templating.

    The :py:exc:`Jinja2TemplatedException` exception extends the standard Python
    generic :py:exc:`Exception` exception class in the same way as
    :py:exc:`TemplatedException`, with the exception of using the templating
    engine of the external Jinja2 package, rather than Python's built-in PEP 3101
    advanced string formatting.

    The template can be configured as a the :py:data:`TEMPLATE`
    class attribute, using the Jinja2 templating language (see
    `external Jinja2 documentation <https://jinja.palletsprojects.com/>`_ to
    learn more).

    .. code-block::python
       :linenos:
       lineno-start: 1

       class OtherNonEmptyListException(Jinja2TemplatedException, RuntimeError):
           TEMPLATE = "The list you provided had {{ len(lst) }} items."

       raise OtherNonEmptyListException(lst=[1, 2, 3])

    As with :py:exc:`TemplatedException`, compatibility with standard exceptions
    is maintained by allowing every descendant of :py:exc:`Jinja2TemplatedException`
    to also be initialized using a single, unnamed parameter for the full message
    of the exception.

    .. code-block::python
       :linenos:
       lineno-start: 5

       raise OtherNonEmptyListException("some msg without templating")
    """

    @classmethod
    def _check_jinja2(cls) -> None:
        if not _HAS_JINJA_2:
            raise ModuleNotFoundError(
                "jinja2 does not seem to be available in this Python environment, "
                "and is necessary for Jinja2TemplatedException; use TemplatedException "
                "instead or add jinja2 as a dependency",
            )

    @classmethod
    def _template_render(
        cls,
        template: str,
        jinja2_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
        **kwargs
    ) -> typing.Optional[str]:
        """
        Render a template with provided keyword arguments, using class' template engine.

        :param template: The Jinja2 template to use
        :param jinja2_kwargs: Optional keyword arguments to pass to the Jinja2
            template constructor
        :param **kwargs: The dictionary to pass to the templating engine

        :return: The rendered template or :py:data:`None` if no template is defined

        :raises TemplatedExceptionInternalRuntimeError: If there are any
            unresolved issues when rendering the template (such as a syntactically
            invalid template; or missing template variables)
        """

        # anticipate most likely error!
        if template is None:
            return

        # checking if jinja2 seems installed

        Jinja2TemplatedException._check_jinja2()

        # try to create the Jinja2 template

        try:
            jinja2_kwargs = jinja2_kwargs or dict()
            jinja2_template = jinja2.Template(
                source=template,
                **(jinja2_kwargs or dict()),
            )
        except Exception as exc:
            raise TemplatedExceptionInternalRuntimeError(
                "Jinja2 template issue while initializing exception message",
            ) from exc

        try:
            ret = jinja2_template.render(**kwargs)
            return ret

        except jinja2.TemplateError as exc:
            # templating problem
            raise TemplatedExceptionInternalRuntimeError(
                "template issue while rendering (Jinja2) templated exception message",
            ) from exc

        except Exception as exc:
            # other problem
            raise TemplatedExceptionInternalRuntimeError(
                "unexpected error while rendering (Jinja2) templated exception message",
            ) from exc

    def __init__(self, *args, passthrough: bool = False, **kwargs):
        """
        Initialize templated exception, with template variables as keyword arguments.

        :param args: For backwards compatibility, allow unnamed arguments
        :param passthrough: Flag to pre-render the template, and pass it as a
            string to the base exception class
        :param kwargs: The template variables provided as keyword arguments
        :raises ModuleNotFoundError: If the required :py:mod:`jinja2` module
            cannot be imported
        """

        # checking if jinja2 seems installed

        Jinja2TemplatedException._check_jinja2()

        # calling the TemplatedException constructor

        super().__init__(
            *args,
            passthrough=passthrough,
            **kwargs,
        )
