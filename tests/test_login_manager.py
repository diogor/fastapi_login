from http.cookies import SimpleCookie
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from starlette.responses import Response

from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from tests.app import load_user, manager, fake_db, TOKEN_URL, NotAuthenticatedException, cookie_manager


async def async_load_user(email):
    return load_user(email)


# TESTS
# TODO: add tests
#  for expired tokens
#  for cookie and header support at the same time

@pytest.mark.asyncio
@pytest.mark.parametrize('function', [load_user, async_load_user])
async def test_user_loader(function, client, default_token):
    # set user loader callback
    manager.user_loader(function)

    user = await manager.get_current_user(default_token)
    assert user['email'] == 'john@doe.com'
    assert user == fake_db['john@doe.com']


@pytest.mark.asyncio
async def test_bad_credentials(client):
    response = await client.post('/auth/token', form=dict(username='invald@e.mail', password='invalidpw'))
    assert response.status_code == 401
    assert response.json()['detail'] == InvalidCredentialsException.detail


@pytest.mark.asyncio
@pytest.mark.parametrize('data', [
    {'invalid': 'token-format'},
    {'sub': 'invalid-username'}
])
async def test_bad(data):
    bad_token = manager.create_access_token(
        data=data
    )
    with pytest.raises(Exception):
        try:
            await manager.get_current_user(bad_token)
        except HTTPException:
            raise Exception
        else:
            # test failed
            assert False


@pytest.mark.asyncio
async def test_no_user_callback(default_token):
    manager._user_callback = None
    with pytest.raises(Exception):
        try:
            await manager.get_current_user(default_token)
        except HTTPException:
            raise Exception
        else:
            assert False

    manager.user_loader(load_user)


@pytest.mark.asyncio
async def test_protector(client, default_token):
    response = await client.get(
        '/protected',
        headers={'Authorization': f'Bearer {default_token}'}
    )
    assert response.json()['status'] == 'Success'


@pytest.mark.asyncio
async def test_cookie_protector(client):
    cookie_resp = await client.post(
        TOKEN_URL, query_string={'cookie': True},
        form=dict(username='john@doe.com', password='hunter2')
    )

    response = await client.get(
        '/protected/cookie',
        cookies=cookie_resp.cookies
    )

    assert response.json()['status'] == 'Success'


@pytest.mark.asyncio
@pytest.mark.parametrize('data', [
    (manager, '/protected'),
    (cookie_manager, '/protected/cookie')
])
async def test_not_authenticated_exception(data, client):
    curr_manager, url = data
    curr_manager.not_authenticated_exception = NotAuthenticatedException
    # cookie_jar is persisted from tests before -> clear
    client.cookie_jar = SimpleCookie()
    resp = await client.get(
        url
    )
    assert resp.json()['data'] == 'redirected'


def test_token_from_cookie_return():
    m = Mock(cookies={'access-token': ''})

    cookie = manager._token_from_cookie(m)
    assert cookie is None

def test_token_from_cookie_exception():
    # reset from tests before, asssume no custom exception has been set
    manager.auto_error = True
    m = Mock(cookies={'access-token': ''})
    with pytest.raises(HTTPException):
        manager._token_from_cookie(m)


def test_set_cookie(default_token):
    response = Response()
    manager.set_cookie(response, default_token)
    assert response.headers['set-cookie'].startswith(f"{manager.cookie_name}={default_token}")


def test_no_cookie_and_no_header_exception():
    with pytest.raises(Exception):
        LoginManager('secret', 'login', use_cookie=False, use_header=False)