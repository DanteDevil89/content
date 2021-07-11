
import demistomock as demisto  # noqa: E402 lgtm [py/polluting-import]
from CommonServerPython import *  # noqa: E402 lgtm [py/polluting-import]
from typing import Dict, Any
import traceback


def check_components(components: list, context: Any):
    """
    Args:
        components(list): list of components related to one field to search
        context: context to check the fields in
    """
    for component in components:
        if isinstance(context, list) and context:
            for x in context:
                check_components(components[components.index(component):], x)
                return
        else:
            context = context[component]


def check_fields(fields_to_search_array: list, context_json) -> bool:
    """
    Args:
        fields_to_search_array(list): list of fields to search
        context_json: context to check the fields in

    Returns: True if all fields are in context_json, else false.
    """
    try:
        for fields in fields_to_search_array:
            components = fields.split('.')
            new_context = context_json
            check_components(components, new_context)

    except Exception:
        return False
    return True


def check_fields_command(args: Dict[str, Any]) -> CommandResults:
    """
    Args:
        args(dict): args from demisto

    Returns: Command Results with context and human readable output
    """
    fields_to_search = args.get('fields_to_search', '')
    context = args.get('context', '{}')

    fields_to_search_array = [field.strip() for field in fields_to_search.split(',')]

    if not fields_to_search:
        raise ValueError('fields_to_search not specified')
    if not context:
        raise ValueError('context not specified')

    # Call the standalone function and get the raw response
    result = check_fields(fields_to_search_array, context)
    readable_output = f'Fields {",".join(fields_to_search_array)} are in given context.' if result \
        else 'There are some fields that not in context.'

    return CommandResults(
        outputs_prefix='CheckIfFieldsExists.FieldsExists',
        outputs_key_field='',
        outputs=result,
        readable_output=readable_output
    )


def main():
    try:
        return_results(check_fields_command(demisto.args()))
    except Exception as ex:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute CheckIfFieldsExists. Error: {str(ex)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
