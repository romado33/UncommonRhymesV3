import os, pytest
from rhyme_core.search import search_all_categories

TERMS = [""double"", ""habit"", ""paper""]  # replace with full list when ready

@pytest.mark.parametrize(""term"", TERMS)
def test_counts(term):
    res = search_all_categories(term)
    assert len(res[""uncommon""]) >= 10
    assert len(res[""slant""]) >= 10
    assert len(res[""multiword""]) >= 10
    if os.getenv(""UR_RAP_DB""):
        assert len(res[""rap_targets""]) >= 10
    else:
        pytest.skip(""rap db not configured"")
