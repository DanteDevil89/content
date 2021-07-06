import pytest
import json
import io
from CommonServerPython import DemistoException, Common

TAG_IDS_LISTS = [([1, 2, 3], [2, 3, 4, 5], [1, 2, 3], [4, 5]),
                 ([1, 2, 3], [4, 5], [1, 2, 3], [4, 5])]

ATTRIBUTE_TAG_LIMIT = [{'ID': '1', 'Name': 'Tag1'}, {'ID': '2', 'Name': 'misp-galaxy:tag2'},
                       {'ID': '3', 'Name': 'misp-galaxy:tag3'}]
INVALID_HASH_ERROR = "Invalid hash length, enter file hash of format MD5, SHA-1 or SHA-256'"
REPUTATION_COMMANDS_ERROR_LIST = [
    ("FILE", "invalid_hash", INVALID_HASH_ERROR),  # invalid HASH,
    ("IP", "1.2.3", "Error: The given IP address: 1.2.3 is not valid"),  # invalid IP,
    ("DOMAIN", "invalid_domain", "Error: The given domain: invalid_domain is not valid"),  # invalid DOMAIN,
    ("URL", "invalid_url", "Error: The given url: invalid_url is not valid"),  # invalid URL,
    ("EMAIL", "invalid_email", "Error: The given invalid_email address: example is not valid"),  # invalid EMAIL,
]

CASE_OF_MALICIOUS_ATTRIBUTE = (['1'], ['2'], ['1'], ['4'], Common.DBotScore.BAD)
CASE_OF_SUSPICIOUS_ATTRIBUTE = (['1'], ['2'], ['2'], ['1'], Common.DBotScore.SUSPICIOUS)
CASE_OF_MALICIOUS_EVENT = (['8'], ['2'], ['2'], ['1'], Common.DBotScore.BAD)
CASE_OF_SUSPICIOUS_EVENT = (['8'], ['2'], ['3'], ['2'], Common.DBotScore.SUSPICIOUS)
CASE_OF_UNKNOWN = (['1'], ['2'], ['3'], ['4'], Common.DBotScore.NONE)
TEST_TAG_SCORES = [CASE_OF_MALICIOUS_ATTRIBUTE, CASE_OF_SUSPICIOUS_ATTRIBUTE, CASE_OF_MALICIOUS_EVENT,
                   CASE_OF_SUSPICIOUS_EVENT, CASE_OF_UNKNOWN]

VALID_DISTRIBUTION_LIST = [(0, 0), ("1", 1), ("Your_organisation_only", 0)]
INVALID_DISTRIBUTION_LIST = ["invalid_distribution", 1.5, "53.5"]

TEST_PREPARE_ARGS = [({'type': '1', 'to_ids': 0, 'from': '2', 'to': '3', 'event_id': '4', 'last': '5',
                       'include_decay_score': 0, 'include_sightings': 0, 'include_correlations': 0,
                       'enforceWarninglist': 0, 'tags': 'NOT:param3', 'value': 6, 'category': '7', 'limit': 10,
                       'org': 7}, {'type_attribute': '1', 'to_ids': 0, 'from_date': '2', 'to_date': '3',
                                   'eventid': ['4'], 'publish_timestamp': '5', 'include_decay_score': 0,
                                   'include_sightings': 0, 'include_correlations': 0, 'enforceWarninglist': 0,
                                   'limit': 10, 'tags': {'NOT': ['param3']}, 'org': 7, 'value': 6, 'category': '7'}),
                     ({}, {'limit': '50'})  # default value
                     ]


def util_load_json(path):
    with io.open(path, mode="r", encoding="utf-8") as f:
        return json.loads(f.read())


def mock_misp(mocker):
    from pymisp import ExpandedPyMISP
    mocker.patch.object(ExpandedPyMISP, '__init__', return_value=None)


def test_convert_timestamp(mocker):
    mock_misp(mocker)
    from MISPV3 import convert_timestamp
    assert convert_timestamp(1546713469) == "2019-01-05 18:37:49"


def test_build_list_from_dict(mocker):
    mock_misp(mocker)
    from MISPV3 import build_list_from_dict
    lst = build_list_from_dict({'ip': '8.8.8.8', 'domain': 'google.com'})
    assert lst == [{'ip': '8.8.8.8'}, {'domain': 'google.com'}]


def test_extract_error(mocker):
    mock_misp(mocker)
    from MISPV3 import extract_error
    error_response = [
        (
            403,
            {
                'name': 'Could not add object',
                'message': 'Could not add object',
                'url': '/objects/add/156/',
                'errors': 'Could not save object as at least one attribute has failed validation (ip). \
                        {"value":["IP address has an invalid format."]}'
            }
        )
    ]
    expected_response = [
        {
            'code': 403,
            'message': 'Could not add object',
            'errors': 'Could not save object as at least one attribute has failed validation (ip).      '
                      '                   {"value":["IP address has an invalid format."]}'
        }
    ]
    err = extract_error(error_response)
    assert err == expected_response

    error_response = [(404, {'name': 'Invalid event.', 'message': 'Invalid event.', 'url': '/objects/add/1546'})]
    expected_response = [{'code': 404, 'message': 'Invalid event.', 'errors': None}]
    err = extract_error(error_response)
    assert err == expected_response

    # Empty error
    err = extract_error([])
    assert err == []


def test_build_misp_complex_filter(mocker):
    mock_misp(mocker)
    from MISPV3 import build_misp_complex_filter

    old_query = "tag1"
    old_query_with_ampersand = "tag1&&tag2"
    old_query_with_not = "!tag1"

    actual = build_misp_complex_filter(old_query)
    assert actual == old_query

    actual = build_misp_complex_filter(old_query_with_ampersand)
    assert actual == old_query_with_ampersand

    actual = build_misp_complex_filter(old_query_with_not)
    assert actual == old_query_with_not

    complex_query_AND_single = "AND:tag1"
    expected = {'AND': ['tag1']}
    actual = build_misp_complex_filter(complex_query_AND_single)
    assert actual == expected

    complex_query_OR_single = "OR:tag1"
    expected = {'OR': ['tag1']}
    actual = build_misp_complex_filter(complex_query_OR_single)
    assert actual == expected

    complex_query_NOT_single = "NOT:tag1"
    expected = {'NOT': ['tag1']}
    actual = build_misp_complex_filter(complex_query_NOT_single)
    assert actual == expected

    complex_query_AND = "AND:tag1,tag2"
    expected = {'AND': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_AND)
    assert actual == expected

    complex_query_OR = "OR:tag1,tag2"
    expected = {'OR': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_OR)
    assert actual == expected

    complex_query_NOT = "NOT:tag1,tag2"
    expected = {'NOT': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_NOT)
    assert actual == expected

    complex_query_AND_OR = "AND:tag1,tag2;OR:tag3,tag4"
    expected = {'AND': ['tag1', 'tag2'], 'OR': ['tag3', 'tag4']}
    actual = build_misp_complex_filter(complex_query_AND_OR)
    assert actual == expected

    complex_query_OR_AND = "OR:tag3,tag4;AND:tag1,tag2"
    expected = {'OR': ['tag3', 'tag4'], 'AND': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_OR_AND)
    assert actual == expected

    complex_query_AND_NOT = "AND:tag1,tag2;NOT:tag3,tag4"
    expected = {'AND': ['tag1', 'tag2'], 'NOT': ['tag3', 'tag4']}
    actual = build_misp_complex_filter(complex_query_AND_NOT)
    assert actual == expected

    complex_query_NOT_AND = "NOT:tag3,tag4;AND:tag1,tag2"
    expected = {'NOT': ['tag3', 'tag4'], 'AND': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_NOT_AND)
    assert actual == expected

    complex_query_OR_NOT = "OR:tag1,tag2;NOT:tag3,tag4"
    expected = {'OR': ['tag1', 'tag2'], 'NOT': ['tag3', 'tag4']}
    actual = build_misp_complex_filter(complex_query_OR_NOT)
    assert actual == expected

    complex_query_NOT_OR = "NOT:tag3,tag4;OR:tag1,tag2"
    expected = {'NOT': ['tag3', 'tag4'], 'OR': ['tag1', 'tag2']}
    actual = build_misp_complex_filter(complex_query_NOT_OR)
    assert actual == expected

    complex_query_AND_OR_NOT = "AND:tag1,tag2;OR:tag3,tag4;NOT:tag5"
    expected = {'AND': ['tag1', 'tag2'], 'OR': ['tag3', 'tag4'], 'NOT': ['tag5']}
    actual = build_misp_complex_filter(complex_query_AND_OR_NOT)
    assert actual == expected


def test_is_tag_list_valid(mocker):
    mock_misp(mocker)
    from MISPV3 import is_tag_list_valid
    is_tag_list_valid(["200", 100])
    assert True


def test_is_tag_list_invalid(mocker):
    mock_misp(mocker)
    from MISPV3 import is_tag_list_valid
    with pytest.raises(DemistoException) as e:
        is_tag_list_valid(["abc", 100, "200"])
        if not e:
            assert False


@pytest.mark.parametrize('malicious_tag_ids, suspicious_tag_ids, return_malicious_tag_ids, return_suspicious_tag_ids',
                         TAG_IDS_LISTS)
def test_handle_tag_duplication_ids(mocker, malicious_tag_ids, suspicious_tag_ids, return_malicious_tag_ids,
                                    return_suspicious_tag_ids):
    mock_misp(mocker)
    from MISPV3 import handle_tag_duplication_ids
    assert return_malicious_tag_ids, return_suspicious_tag_ids == handle_tag_duplication_ids(malicious_tag_ids,
                                                                                             suspicious_tag_ids)


def test_convert_arg_to_misp_args(mocker):
    mock_misp(mocker)
    from MISPV3 import convert_arg_to_misp_args
    args = {'dst_port': 8001, 'src_port': 8002, 'name': 'test'}
    args_names = ['dst_port', 'src_port', 'name']
    assert convert_arg_to_misp_args(args, args_names) == [{'dst-port': 8001}, {'src-port': 8002}, {'name': 'test'}]


def test_pagination_args_valid(mocker):
    mock_misp(mocker)
    from MISPV3 import pagination_args_validation
    pagination_args_validation("5", 50)
    assert True


def test_pagination_args_invalid(mocker):
    mock_misp(mocker)
    from MISPV3 import pagination_args_validation
    with pytest.raises(DemistoException) as e:
        pagination_args_validation("page", "3")
        if not e:
            assert False


@pytest.mark.parametrize('dbot_type, value, error_expected', REPUTATION_COMMANDS_ERROR_LIST)
def test_reputation_value_validation(mocker, dbot_type, value, error_expected):
    mock_misp(mocker)
    from MISPV3 import reputation_value_validation
    with pytest.raises(SystemExit) as e:
        reputation_value_validation(value, dbot_type)
        assert error_expected in str(e.value)


@pytest.mark.parametrize('distribution_id, expected_distribution_id', VALID_DISTRIBUTION_LIST)
def test_get_valid_distribution(mocker, distribution_id, expected_distribution_id):
    mock_misp(mocker)
    from MISPV3 import get_valid_distribution
    assert get_valid_distribution(distribution_id) == expected_distribution_id


@pytest.mark.parametrize('distribution_id', INVALID_DISTRIBUTION_LIST)
def test_get_invalid_distribution(mocker, distribution_id):
    mock_misp(mocker)
    from MISPV3 import get_valid_distribution
    with pytest.raises(SystemExit) as e:
        get_valid_distribution(distribution_id)
        if not e:
            assert False


@pytest.mark.parametrize('event_id', ['event_id', 23.4])
def test_get_invalid_event_id(mocker, event_id):
    mock_misp(mocker)
    from MISPV3 import get_valid_event_id
    with pytest.raises(SystemExit) as e:
        get_valid_event_id(event_id)
        if not e:
            assert False


@pytest.mark.parametrize('is_event_level, expected_output, expected_tag_list_ids', [
    (False, ATTRIBUTE_TAG_LIMIT, {'1', '3'}),
    (True, ATTRIBUTE_TAG_LIMIT, {'1', '3', '2'})])
def test_limit_tag_output(mocker, is_event_level, expected_output, expected_tag_list_ids):
    mock_misp(mocker)
    from MISPV3 import limit_tag_output
    mock_tag_json = util_load_json("test_data/Attribute_Tags.json")
    outputs, tag_list_id = limit_tag_output(mock_tag_json, is_event_level)
    assert outputs == expected_output
    assert tag_list_id == expected_tag_list_ids


@pytest.mark.parametrize('attribute_tags_ids, event_tags_ids, malicious_tag_ids, suspicious_tag_ids, expected_score',
                         TEST_TAG_SCORES)
def test_get_score_by_tags(mocker, attribute_tags_ids, event_tags_ids, malicious_tag_ids, suspicious_tag_ids,
                           expected_score):
    mock_misp(mocker)
    from MISPV3 import get_score_by_tags
    assert get_score_by_tags(attribute_tags_ids, event_tags_ids, malicious_tag_ids,
                             suspicious_tag_ids) == expected_score


def test_event_response_to_markdown_table(mocker):
    mock_misp(mocker)
    from MISPV3 import event_response_to_markdown_table
    event_response = util_load_json("test_data/event_response_to_md.json")
    md = event_response_to_markdown_table(event_response)[0]
    assert md['Event ID'] == '1'
    assert md['Event Tags'] == ["Tag1", "misp-galaxy:tag2", "misp-galaxy:tag3"]
    assert md['Event Galaxies'] == ["galaxy1", "galaxy2"]
    assert md['Event Objects'] == ["obj1", "obj2"]
    assert md['Publish Timestamp'] == '2021-06-16 08:35:01'
    assert md['Event Info'] == 'Test'
    assert md['Event Org ID'] == '1'
    assert md['Event Orgc ID'] == '8'
    assert md['Event Distribution'] == '0'
    assert md['Event UUID'] == '5e6b322a-9f80-4e2f-9f2a-3cab0a123456'


def test_attribute_response_to_markdown_table(mocker):
    mock_misp(mocker)
    from MISPV3 import attribute_response_to_markdown_table
    attribute_response = util_load_json("test_data/attribute_response_to_md.json")
    md = attribute_response_to_markdown_table(attribute_response)[0]
    assert md['Attribute ID'] == "1"
    assert md['Event ID'] == "2"
    assert md['Attribute Category'] == "Payload delivery"
    assert md['Attribute Type'] == "md5"
    assert md['Attribute Value'] == "6c73d338ec64e0e44bd54ea123456789"
    assert md['Attribute Tags'] == ["Tag1", "misp-galaxy:tag2", "misp-galaxy:tag3"]
    assert md['To IDs'] is True
    assert md['Event Info'] == 'Test'
    assert md['Event Organisation ID'] == '1'
    assert md['Event Distribution'] == '0'
    assert md['Event UUID'] == '5e6b322a-9f80-4e2f-9f2a-3cab0a123456'


def test_parse_response_reputation_command(mocker):
    mock_misp(mocker)
    from MISPV3 import parse_response_reputation_command
    reputation_response = util_load_json("test_data/reputation_command_response.json")
    reputation_expected = util_load_json("test_data/reputation_command_outputs.json")
    malicious_tag_ids = ['279', '131']
    suspicious_tag_ids = ['104']
    outputs, _ = parse_response_reputation_command(reputation_response, malicious_tag_ids, suspicious_tag_ids)
    assert outputs == reputation_expected


@pytest.mark.parametrize('demisto_args, expected_args', TEST_PREPARE_ARGS)
def test_prepare_args_to_search(mocker, demisto_args, expected_args):
    mock_misp(mocker)
    from MISPV3 import prepare_args_to_search
    import demistomock
    mocker.patch.object(demistomock, 'args', return_value=demisto_args)
    assert prepare_args_to_search() == expected_args


def test_build_events_search_response(mocker):
    mock_misp(mocker)
    from MISPV3 import build_events_search_response, ENTITIESDICT
    search_response = util_load_json("test_data/search_event_by_tag.json")
    search_expected_output = util_load_json("test_data/search_event_by_tag_outputs.json")
    search_outputs = build_events_search_response(search_response)
    for actual_event, expected_event in zip(search_outputs, search_expected_output):
        for key, event_field in ENTITIESDICT.items():
            if actual_event.get(event_field):
                assert actual_event.get(event_field) == expected_event.get(event_field)


def test_build_attributes_search_response(mocker):
    mock_misp(mocker)
    from MISPV3 import build_attributes_search_response, ENTITIESDICT
    search_response = util_load_json("test_data/search_attribute_by_type.json")
    search_expected_output = util_load_json("test_data/search_attribute_by_type_outputs.json")
    search_outputs = build_attributes_search_response(search_response)
    for actual_attribute, expected_attribute in zip(search_outputs, search_expected_output):
        for key, event_field in ENTITIESDICT.items():
            if actual_attribute.get(event_field):
                assert actual_attribute.get(event_field) == expected_attribute.get(event_field)
