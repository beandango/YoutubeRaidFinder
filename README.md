# YouTube Raid Finder 🪄🔴

![CI](https://github.com/beandango/YoutubeRaidFinder/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/beandango/YoutubeRaidFinder/branch/main/graph/badge.svg)

A Flask web-app that lets VTubers (or anyone who streams) **discover live YouTube channels to raid/live redirect into** based on:

* viewer count & subscriber count  
* detected language (FastText `lid.176.bin`)  
* optional “VTuber” keyword filter
* any other search terms (games, art, etc)
* personal “Favourite channels” list

## See the releases tab for the latest build :)
* Feel free to create an issue for bugs, feature ideas, questions, and more


![raidfinder](https://github.com/user-attachments/assets/cb9e0c01-d552-43cb-afe2-1083271eaeac)

## ✨ Quick start (local dev)

```bash
git clone https://github.com/beandango/YoutubeRaidFinder.git
cd YoutubeRaidFinder
```

## 1) Python env
```bash
python -m venv
```
```
.venv\Scripts\activate
```
```
pip install -r requirements-dev.txt
```
```
playwright install --with-deps                     
```
## 2) API key & model
**See `How to set up Youtube Raid Finder-3.pdf` for how to get the API key**

```
$api = "put your actual Youtube Data API v3 key here"
>> (Get-Content config.json) -replace "YOUR KEY HERE", $api |
>>     Set-Content config.json
```
* alternatively, you can just replace YOUR KEY HERE with your key in the config.json file manually

```
curl -o example.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
```

## 3) Run it
```python app.py```

## Building the exe
```pyinstaller --name YTRaidFinder --onedir app.py```

* now you just copy the `config.json` , `favorites.json`, `lid.176.bin` files and `static\` and `templates\` folders and paste into the YTRaidFinder folder created in `dist\` (the one with the exe you just made)

