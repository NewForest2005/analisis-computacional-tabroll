from references.sarniezz_corrections import FIRST_RIFF_LAST_NOTE, pitch


def test_sarniezz_first_riff_last_note_is_quarter_sharp():
    assert FIRST_RIFF_LAST_NOTE == pitch("D#+") == 3.5
    assert FIRST_RIFF_LAST_NOTE != 3.0  # Re# natural
