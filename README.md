
1. install python trello api `pip install trello`
1. create an app key by visiting https://trello.com/app-key
1. create an unlimted time,readonly token, by visiting https://trello.com/1/authorize?key=REPLACE_WITH_KEY_FROM_PREVIOUS_STEP&name=trello-export&expiration=never&response_type=token
1. create a config file in `~/.trello` or wherever you prefer with the content of
```
[trello]
API_KEY = replace_with_api_key
API_TOKEN = replace_with_api_token
```
1. run `./trello-export -b "board name" -l "list name"` use the `-c path_to_config` flag if you wont be using default of `~/.trello`
