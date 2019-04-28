import asyncio

import pytest

from .conftest import connect_and_sign_in, read_until


@pytest.mark.slow
async def test_game_matchmaking(loop, lobby_server, mocker):
    mocker.patch('server.ladder_service.asyncio.sleep', return_value=asyncio.sleep(0.5))
    _, _, proto1 = await connect_and_sign_in(
        ('ladder1', 'ladder1'), lobby_server
    )
    _, _, proto2 = await connect_and_sign_in(
        ('ladder2', 'ladder2'), lobby_server
    )

    await read_until(proto1, lambda msg: msg['command'] == 'game_info')
    await read_until(proto2, lambda msg: msg['command'] == 'game_info')

    proto1.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'uef'
    })
    await proto1.drain()

    proto2.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'uef'
    })
    await proto2.drain()

    # If the players did not match, this test will fail due to a timeout error
    msg1 = await read_until(proto1, lambda msg: msg['command'] == 'game_launch')
    msg2 = await read_until(proto2, lambda msg: msg['command'] == 'game_launch')

    assert msg1['uid'] == msg2['uid']
    assert msg1['mod'] == 'ladder1v1'
    assert msg2['mod'] == 'ladder1v1'


async def test_game_matchmaking_ban(loop, lobby_server, db_engine):
    _, _, proto = await connect_and_sign_in(
        ('ladder_ban', 'ladder_ban'), lobby_server
    )

    await read_until(proto, lambda msg: msg['command'] == 'game_info')

    proto.send_message({
        'command': 'game_matchmaking',
        'state': 'start',
        'faction': 'uef'
    })
    await proto.drain()

    # This may fail due to a timeout error
    msg = await read_until(proto, lambda msg: msg['command'] == 'notice')

    assert msg == {
        'command': 'notice',
        'style': 'error',
        'text': 'You are banned from the matchmaker. Contact an admin to have the reason.'
    }
