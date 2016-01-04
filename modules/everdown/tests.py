from everfetch import Everfetch, memoize, rate_limit
from evernote.edam.error.ttypes import EDAMSystemException, EDAMErrorCode
from mock import Mock


def test_memoize():
    """ memoize decorator should cache the return value passing through any arguments """
    mock_f = Mock(return_value='value')

    # Mock doesn't provide a name, and crashes if you try to access it
    mock_f.__name__ = 'mock_f'

    memoized_mock_f = memoize(mock_f)

    # Function should have the same name
    assert memoized_mock_f.__name__ == 'mock_f'

    # A single call should pass through arguments and return the value
    assert memoized_mock_f('any arguments', should='work') == 'value'
    mock_f.assert_called_once_with('any arguments', should='work')

    # An additional call shouldn't call the original function again
    assert memoized_mock_f('new arguments', should_still='work') == 'value'
    assert mock_f.call_count == 1


# @patch('everfetch.sleep')
# def test_rate_limit(sleep):
def test_rate_limit():
    # Patch out sleep with a mock
    import everfetch
    orig_sleep = everfetch.sleep
    everfetch.sleep = sleep = Mock()

    # Ensure that the test function times out the first time it is called
    def timeout_once():
        if not timeout_once.__timed_out:
            timeout_once.__timed_out = True
            raise EDAMSystemException(
                errorCode=EDAMErrorCode.RATE_LIMIT_REACHED,
                rateLimitDuration=5)
        return 'value'
    timeout_once.__timed_out = False

    # Func will pretend to be rate limited
    func = Mock(side_effect=timeout_once)

    rate_limited_func = rate_limit(func)

    # Should eventually return the correct value
    assert rate_limited_func() == 'value'

    # Should sleep if rate limited, the rateLimitDuration plus magic 2 seconds
    sleep.assert_called_once_with(5 + 2)

    # Restore old sleep
    everfetch.sleep = orig_sleep


def test_everfetch_init():
    ef = Everfetch(token='token', token_sandbox='token_sandbox', sandbox=False)
    assert ef.token == 'token'
    ef = Everfetch(token='token', token_sandbox='token_sandbox', sandbox=True)
    assert ef.token == 'token_sandbox'

# def test_everfetch_note_store
# Should return a note store, and the same note store

# def test_everfetch_fetch_all_notebooks
# Test network call

# def test_everfetch_fetch_note_metadata_page
# Test network call

# def test_everfetch_fetch_note
# Test network call

# def test_everfetch_fetch_note_metadata
# Mock: fetch_notebooks
# Mock: fetch_note_metadata_from_notebook
# Test yeilds all of them

# def test_everfetch_fetch_notebooks
#