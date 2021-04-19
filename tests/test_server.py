import pytest
import codes


@pytest.mark.parametrize(
    ('user', 'result'),
    (
        ('ash', codes.LOGGED_IN),
        ('', codes.NOT_LOGGED_IN),
    )
)
def test_user(client, user, result):
    user = client.user_pi_command(b'USER ' + bytes(user, 'utf-8'))
    assert user == result.decode('utf-8')
