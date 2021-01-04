# Templated Exceptions

## Example

A templated exception is an exception class which, instead of taking a static
message when initialized/raised (as typical Python exception classes are used),
is defined with a template and provided only template variables when raised.

For instance, in this example, we define an `ExampleRuntimeException` to report
on errors related to the command-line parameters provided to a program:

```python
import templated_exceptions

class ExampleRuntimeException(templated_exceptions.TemplatedException, RuntimeError):
    TEMPLATE = "Program unexpectedly failed with input args: {args}."

raise ExampleRuntimeException(args=["myprogram", "-e", "--badflag"])
```

will produce the following exception stack trace:

```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ExampleRuntimeException: Program unexpectedly failed with input args: ['myprogram', '-e', '--badflag'].
```
