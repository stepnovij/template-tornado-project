## Evaluate basic usage:
To evaluate text send a POST request to '$HOST/ai/text/evaluate'. Specify data_set_id, provider_id 
and scoring type as in the following example:

```sh
curl -XPOST -H 'apikey: YOUR_API_KEY' '$HOST/ai/text/evaluate' -d '{
 "context": {
  "data_set_id": "1",
  "score_type": "bleu"
 },
 "service": {
  "provider": "ai.text.translate.microsoft.translator_text_api.2-0"
 }
}'
```

The response contains the translated text and score type:

```sh
{
 "results": ["some translation1", "some translation2"],
 "score": {
    "type": "bleu",
    "value": "0.75"
 }
 "meta": {
    "source_language": "en",
    "targe_language": "ru"
 },
 "service": {
  "provider": {
   "id": "ai.text.translate.microsoft.translator_text_api.2-0",
   "name": "Microsoft Translator API"
  }
 }
}
```

In the multi mode, the translation of the text is performed using a list of providers. The mode is activated by passing an array of provider identificators.


```sh
curl -XPOST -H 'apikey: YOUR_API_KEY' '$HOST/ai/text/evaluate' -d '{
 "context": {
  "data_set_id": "1",
  "score_type": "bleu"
 },
 "service": {
  "provider": ["ai.text.translate.microsoft.translator_text_api.2-0", "ai.text.translate.yandex.translate_api.1-5"]
 }
}'
```

The response contains the translated text and a service information: ↑

```sh
[
{
 "results": ["some translation1", "some translation2"],
 "score": {
    "type": "bleu",
    "value": "0.75"
 }
 "meta": {
    "source_language": "en",
    "targe_language": "ru"
 },
 "service": {
  "provider": {
   "id": "ai.text.translate.microsoft.translator_text_api.2-0",
   "name": "Microsoft Translator API"
  }
 }
},
{
 "results": ["some translation1", "some translation2"],
 "score": {
    "type": "bleu",
    "value": "0.86"
 }
 "meta": {
    "source_language": "en",
    "targe_language": "ru"
 },
 "service": {
  "provider": {
   "id": "ai.text.translate.yandex.translate_api.1-5",
   "name": "Yandex Translate API"
  }
 }
}
]
```