import pytest

from storage import DataSet, DefaultStorage, Manager


@pytest.fixture
def create_storage(tmpdir):
    return DefaultStorage(data_set_base_path=str(tmpdir),
                          results_base_path=str(tmpdir))


@pytest.fixture
def manager(create_storage):
    return Manager(storage=create_storage)


@pytest.fixture
def provider_id():
    return 'some.provider.id'


@pytest.fixture
def data_set_id():
    return 1


@pytest.fixture
def data_set_name():
    return 'en-ru'


@pytest.fixture
def translation_result():
    text = (
        """Социальная карта жителя Ивановской области признается """
        """электронным средством платежа."""
    )
    return {
        "results": [text, text],
        "meta": {},
        "service": {
            "provider": {
                "id": "ai.text.translate.microsoft.translator_text_api.2-0",
                "name": "Microsoft Translator API"
            }
        }
    }


@pytest.fixture
def data_set():
    text = (
        """The social card of residents of Ivanovo region is to be recognised """
        """as an electronic payment instrument.	Социальная карта жителя Ивановской области """
        """признается электронным средством платежа."""
    )
    return [text, text]


@pytest.fixture
def data_set_parsed_from_en_to_ru():
    original = ['The social card of residents of Ivanovo region is to be recognised',
                'The social card of residents of Ivanovo region is to be recognised']

    translated = ['Социальная карта жителя Ивановской области признается электронным средством платежа',
                  'Социальная карта жителя Ивановской области признается электронным средством платежа']

    return DataSet(lang_from='en', lang_to='ru', original=original, translation=translated)
