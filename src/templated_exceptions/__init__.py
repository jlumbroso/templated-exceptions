"""
This package makes it easy to define custom exceptions with
templated error messages, such that the exceptions only to
be raised with the differing parameters. This provides excellent
user description of errors, as they can be explained once,
optimized for clarity.
"""

import typing


_HAS_JINJA_2 = True

try:
    import jinja2
except (ImportError, ModuleNotFoundError):
    jinja2 = None
    _HAS_JINJA_2 = False


__author__ = "Jérémie Lumbroso <lumbroso@cs.princeton.edu>"

__version__ = "20.1.0"

__all__ = [
    "TemplatedException",
    "Jinja2TemplatedException",
]


# standard templating engine

class TemplatedException(Exception):

    # CLASS METHODS

    @classmethod
    def _template_render(cls, template, **kwargs):

        try:
            ret = template.format(**kwargs)
            return ret

        except KeyError:
            # missing keys in template
            raise

        except:
            # other problem
            raise

    @classmethod
    def _template(cls, **kwargs) -> typing.Optional[str]:

        try:
            template = getattr(cls, "TEMPLATE")
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

    @classmethod
    def _argnames(cls) -> typing.List[str]:
        template = cls._template()

        argnames = []

        # to guess all the format parameters, we try to
        # render the formatted template and catch KeyError

        while True:
            kwargs = dict(zip(argnames, [""]*len(argnames)))
            try:
                template.format(**kwargs)

            except KeyError as key_error:
                # a key is missing, so we still have to check
                # if there other keys, hence new iteration
                missing = key_error.args[0]
                argnames.append(missing)
                continue

            except:
                # some unexpected error
                pass

            break

        return argnames

    # INSTANCE METHODS

    def __init__(self, *args, passthrough=False, **kwargs):

        self._args = args
        self._kwargs = kwargs

        # Call the BaseException constructor with a prerendered
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
        # in Python 3, the message of an exception is typically
        # stored in args[0]
        try:
            args = getattr(self, "_args")
            return not (args is None or len(args) == 0)
        except AttributeError:
            # there is no attribute called '_args'
            return False

    def __str__(self) -> str:

        rendered_template = self._template(**self._kwargs)

        if self._has_message() or rendered_template is None:
            return super().__str__()

        return rendered_template


# jinja2 templating engine

class Jinja2TemplatedException(TemplatedException):

    @classmethod
    def _template_render(cls, template: str, jinja2_kwargs=None, **kwargs):

        # try to create the Jinja2 template

        try:
            jinja2_kwargs = jinja2_kwargs or dict()
            jinja2_template = jinja2.Template(
                source=template,
                **jinja2_kwargs,
            )
        except Exception as exc:
            raise

        try:
            ret = jinja2_template.render(**kwargs)
            return ret

        except:
            # other problem
            raise

    def __init__(self, *args, passthrough=False, **kwargs):

        # checking if jinja2 seems installed
        if not _HAS_JINJA_2:
            raise ModuleNotFoundError(
                "jinja2 does not seem to be available in this Python environment"
            )

        # calling the TemplatedException constructor

        super().__init__(
            *args,
            passthrough=passthrough,
            **kwargs,
        )
