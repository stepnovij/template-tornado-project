import pytest


@pytest.fixture
def create_data_set(data_set, tmpdir, data_set_name, data_set_id):
    full_path = tmpdir.mkdir(str(data_set_id)).join('{}.txt'.format(data_set_name))
    full_path.write('\n'.join(data_set).encode())
    return full_path


@pytest.mark.asyncio
async def test_create_result(data_set_id, translation_result, manager):
    file_path = await manager.save(data_set_id, translation_result)
    with open(file_path, 'rb') as fd:
        data = fd.read()
        assert data.decode() == '\n'.join(translation_result)


@pytest.mark.asyncio
async def test_open_data_set(data_set_id, translation_result, manager):
    file_path = await manager.save(data_set_id, translation_result)
    with open(file_path, 'rb') as fd:
        data = fd.read()
        assert data.decode() == '\n'.join(translation_result)


@pytest.mark.asyncio
async def test_data_set_handling(create_data_set, manager, data_set_id, data_set):
    opend_data_set = await manager.get_data_set(data_set_id)
    original, translation = data_set[0].split('\t')
    assert original in opend_data_set.original[0]
    assert translation in opend_data_set.translation[0]
