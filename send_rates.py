from datetime import datetime
import os
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import urllib3

# Отключаем предупреждения SSL от локального антивируса/провайдера
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_env(filepath=r"D:\AI scripts\паролимароли\1!.env"):
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


env = load_env()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or env.get(
    "TELEGRAM_BOT_TOKEN", ""
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")

CITIES = [
    ("Краснодар", 45.0355, 38.9753),
    ("Алушта", 44.6764, 34.4100),
    ("Ханчжоу", 30.2741, 120.1551),
]

# Дни недели: (Приветствие RU, Фраза CN, Пиньинь + Русская транскрипция, Разбор дня недели)
WEEKDAYS = {
    0: (
        "Доброе утро! Отличного понедельника!",
        "早上好！祝你星期一愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīyī yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-и юйкуай! (星期一 [син-цзи-и] = понедельник, досл. «день недели №1»)",
    ),
    1: (
        "Доброе утро! Прекрасного вторника!",
        "早上好！祝你星期二愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqī'èr yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-эр юйкуай! (星期二 [син-цзи-эр] = вторник, досл. «день недели №2»)",
    ),
    2: (
        "Доброе утро! Удачной среды!",
        "早上好！祝你星期三愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīsān yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-сань юйкуай! (星期三 [син-цзи-сань] = среда, досл. «день недели №3»)",
    ),
    3: (
        "Доброе утро! Хорошего четверга!",
        "早上好！祝你星期四愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīsì yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-сы юйкуай! (星期四 [син-цзи-сы] = четверг, досл. «день недели №4»)",
    ),
    4: (
        "Доброе утро! С пятницей!",
        "早上好！祝你星期五愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīwǔ yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-у юйкуай! (星期五 [син-цзи-у] = пятница, досл. «день недели №5»)",
    ),
    5: (
        "Доброе утро! Чудесной субботы!",
        "早上好！祝你星期六愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīliù yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-лю юйкуай! (星期六 [син-цзи-лю] = суббота, досл. «день недели №6»)",
    ),
    6: (
        "Доброе утро! Прекрасного воскресенья!",
        "早上好！祝你星期日愉快！",
        "Zǎoshang hǎo! Zhù nǐ xīngqīrì yúkuài!",
        "Цзаошан хао! Чжу ни син-цзи-жи юйкуай! (星期日 [син-цзи-жи] = воскресенье, досл. «день Солнца»)",
    ),
}

# Средний план (MEDIUM SHOT, full body): утка в полный рост и красивый фон вокруг неё
DUCK_STYLES = [
    (
        "3D Pixar мультик",
        "MEDIUM SHOT full body view: a cute yellow 3D Disney Pixar duck standing on a cozy wooden porch with a coffee mug, waving one wing at the viewer, sunny morning garden background, 8k render",
    ),
    (
        "Фото National Geographic",
        "MEDIUM WIDE WILDLIFE PHOTO: a real cute mallard duck standing on a mossy stone by a mountain lake at sunrise, raising one wing like waving hello, scenic morning mist background, National Geographic",
    ),
    (
        "Аниме Studio Ghibli",
        "MEDIUM SHOT anime illustration: a cute white duck in full body standing on a sunny balcony with a teapot, waving its wing happily, scenic green hills and blue sky in background, Studio Ghibli style",
    ),
    (
        "Китайская живопись (Ханчжоу)",
        "MEDIUM SHOT traditional Chinese ink and watercolor painting: a cute duck in full body standing on a bridge waving its wing, scenic West Lake in Hangzhou with lotus flowers and pagoda in background",
    ),
    (
        "Крутой Киберпанк",
        "MEDIUM SHOT full body: a cute yellow duck wearing neon sunglasses and a tiny jacket, standing on a futuristic street and waving its wing, colorful cyberpunk morning city background",
    ),
    (
        "Вязаная игрушка (Амигуруми)",
        "MEDIUM SHOT PHOTO: a handmade knitted yellow amigurumi duck toy in full body standing next to a croissant and tea cup on a sunny wooden table by the window, waving one wing",
    ),
    (
        "Пушистая акварель",
        "MEDIUM SHOT watercolor postcard: a cheerful fluffy duckling in full body standing among morning meadow flowers and waving its wing, soft scenic pastel background",
    ),
    (
        "Фигурка LEGO",
        "MEDIUM SHOT PHOTO: a LEGO brick yellow duck figure in full body standing in a sunny LEGO town square with trees and a bench, waving its wing",
    ),
]


def send_morning_duck():
    ru_greet, cn_chars, pinyin_str, ru_trans = WEEKDAYS[
        datetime.now().weekday()
    ]
    style_name, style_prompt = random.choice(DUCK_STYLES)
    seed = random.randint(1, 999999)

    encoded_prompt = urllib.parse.quote(style_prompt)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&enhance=false&nologo=true"

    caption = (
        f"🦆 <b>{ru_greet}</b>\n\n"
        f"🇨🇳 <b>{cn_chars}</b>\n"
        f"🔤 <i>{pinyin_str}</i>\n"
        f"🗣 {ru_trans}\n\n"
        f"🎨 <i>Стиль дня: {style_name}</i>"
    )
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:
        print(f"Генерирую утку ({style_name})...")
        img_resp = requests.get(img_url, timeout=45, verify=False)
        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
            files = {"photo": ("duck.jpg", img_resp.content, "image/jpeg")}
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            requests.post(tg_url, data=data, files=files, timeout=30)
            print("Утка успешно отправлена!")
        else:
            requests.post(
                tg_url,
                data={
                    "chat_id": CHAT_ID,
                    "photo": img_url,
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                timeout=30,
            )
            print("Утка отправлена через сервер Telegram!")
    except Exception as e:
        print("Переключаюсь на отправку через сервер Telegram...", e)
        requests.post(
            tg_url,
            data={
                "chat_id": CHAT_ID,
                "photo": img_url,
                "caption": caption,
                "parse_mode": "HTML",
            },
            timeout=30,
        )


def get_currencies_and_crypto():
    lines = []
    try:
        val = requests.get(
            "https://www.cbr-xml-daily.ru/daily_json.js", timeout=10
        ).json()["Valute"]
        for code, flag in [("CNY", "🇨🇳"), ("USD", "🇺🇸"), ("EUR", "🇪🇺")]:
            cur = val[code]["Value"]
            diff = cur - val[code]["Previous"]
            sign = "+" if diff > 0 else ""
            lines.append(
                f"• {flag} <b>{code}:</b> {cur:.2f} ₽ ({sign}{diff:.2f})"
            )
    except Exception as e:
        lines.append(f"• Ошибка ЦБ: {e}")

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether&vs_currencies=usd,rub&include_24hr_change=true"
        r = requests.get(url, timeout=10).json()
        usdt_rub = r["tether"]["rub"]
        btc_usd = r["bitcoin"]["usd"]
        btc_chg = r["bitcoin"]["usd_24h_change"]
        sign = "+" if btc_chg >= 0 else ""
        lines.append(f"• 💵 <b>USDT:</b> {usdt_rub:.2f} ₽")
        lines.append(f"• 🪙 <b>BTC:</b> ${btc_usd:,.0f} ({sign}{btc_chg:.1f}%)")
    except Exception as e:
        lines.append(f"• Ошибка крипты: {e}")
    return "\n".join(lines)


def get_alushta_sea_temp():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(
            "https://seatemperature.ru/current/russia/alushta-sea-temperature",
            headers=headers,
            timeout=8,
        ).text
        m = re.search(r"составляет\s*([0-9]+(?:\.[0-9]+)?)\s*°C", html)
        if m:
            return f"+{m.group(1)}°C"
    except Exception:
        pass
    try:
        url = "https://marine-api.open-meteo.com/v1/marine?latitude=44.667&longitude=34.417&current=sea_surface_temperature"
        t = requests.get(url, timeout=6).json()["current"][
            "sea_surface_temperature"
        ]
        if t is not None:
            return f"{t:+.1f}°C"
    except Exception:
        pass
    return "н/д"


def get_weather():
    lines = []
    headers = {"User-Agent": "KavBotWeather/1.0"}
    for name, lat, lon in CITIES:
        try:
            url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
            series = requests.get(url, headers=headers, timeout=10).json()[
                "properties"
            ]["timeseries"]
            now_t = series[0]["data"]["instant"]["details"]["air_temperature"]
            temps_24h = [
                item["data"]["instant"]["details"]["air_temperature"]
                for item in series[:24]
            ]
            max_t, min_t = max(temps_24h), min(temps_24h)
            rain_mm = sum(
                item["data"]
                .get("next_1_hours", {})
                .get("details", {})
                .get("precipitation_amount", 0.0)
                for item in series[:12]
            )
            rain_str = f", ☔️ {rain_mm:.1f} мм" if rain_mm >= 0.5 else ""
            lines.append(
                f"• <b>{name}:</b> сейчас {now_t:+.0f}°C (днём {max_t:+.0f}° / ночью {min_t:+.0f}°{rain_str})"
            )
        except Exception as e:
            lines.append(f"• <b>{name}:</b> ошибка ({e})")
    lines.append(f"• 🌊 <b>Море в Алуште:</b> {get_alushta_sea_temp()}")
    return "\n".join(lines)


def clean_wiki(text):
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"'{2,}", "", text)
    return text.strip(" *—–-:;")


def get_holidays():
    now = datetime.now()
    months = [
        "",
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    page = f"{now.day}_{months[now.month]}"

    ru_hol = "Памятный день календаря"
    cn_wiki_hol = None

    try:
        url = f"https://ru.wikipedia.org/w/api.php?action=parse&page={page}&prop=wikitext&format=json"
        r = requests.get(
            url, headers={"User-Agent": "KavBot/1.0"}, timeout=8
        ).json()
        wikitext = r["parse"]["wikitext"]["*"]

        # Исправленное регулярное выражение: захватывает все подразделы === ... === внутри == Праздники ==
        m = re.search(
            r"==\s*Праздники[^=\n]*==(.*?)(?:\n==\s*[^=\s]|\Z)",
            wikitext,
            re.DOTALL,
        )
        section = m.group(1) if m else wikitext

        ru_list = []
        intl_list = []
        in_ru_block = False

        for raw_line in section.split("\n"):
            line = raw_line.strip()
            if not line.startswith("*"):
                if line.startswith("==="):
                    in_ru_block = False
                continue

            # Проверка вложенных списков вида "* Россия:" -> "** Праздник"
            if line.startswith("* ") and not line.startswith("**"):
                in_ru_block = "Россия" in line or "СССР" in line

            if ("Россия" in line or "СССР" in line) and ":" in line:
                item = clean_wiki(line.split(":", 1)[1])
                if len(item) > 3:
                    ru_list.append(item)
            elif in_ru_block and line.startswith("**"):
                item = clean_wiki(line)
                if len(item) > 3:
                    ru_list.append(item)
            elif ("Китай" in line or "КНР" in line) and ":" in line:
                cn_wiki_hol = clean_wiki(line.split(":", 1)[1])
            elif (
                line.startswith("* ")
                and ":" not in line
                and not line.endswith(":")
            ):
                item = clean_wiki(line)
                if len(item) > 4:
                    intl_list.append(item)

        # Также проверяем секцию народных примет/календаря (например, Дмитриев день)
        m_folk = re.search(
            r"===\s*(?:Приметы|Народный календарь)[^=\n]*===(.*?)(?:\n==|\Z)",
            wikitext,
            re.DOTALL,
        )
        if m_folk:
            for raw_line in m_folk.group(1).split("\n"):
                if raw_line.strip().startswith("*"):
                    folk_item = clean_wiki(raw_line.split("—")[0].split(".")[0])
                    if 3 < len(folk_item) < 45:
                        intl_list.append(f"{folk_item} (народн.)")
                        break

        combined = ru_list + intl_list
        if combined:
            ru_hol = "; ".join(combined[:3])
    except Exception:
        pass

    cn_fixed = {
        (1, 1): "Новый год (元旦 Юаньдань)",
        (2, 14): "Праздник весны / Китайский Новый год (春节)",
        (3, 8): "Международный женский день (妇女节)",
        (3, 12): "День посадки деревьев в КНР (植树节)",
        (4, 4): "Праздник Цинмин (清明节)",
        (5, 1): "День труда (劳动节)",
        (5, 4): "День молодёжи Китая (青年节)",
        (6, 1): "День защиты детей (儿童节)",
        (7, 1): "День основания КПК (建党节)",
        (8, 1): "День НОАК (建军节)",
        (9, 10): "День учителя в Китае (教师节)",
        (10, 1): "День образования КНР (国庆节)",
        (11, 8): "День журналиста в Китае (记者节)",
        (11, 11): "День холостяков / Всемирный день шопинга (双十一)",
    }

    doy = now.timetuple().tm_yday
    solar_terms = [
        (311, "Сезон Лидун (立冬 — «Начало зимы», время пельменей цзяоцзы)"),
        (326, "Сезон Сяосюэ (小雪 — «Малые снега»)"),
        (341, "Сезон Дасюэ (大雪 — «Большие снега»)"),
        (355, "Сезон Дунчжи (冬至 — «Зимнее солнцестояние»)"),
        (296, "Сезон Шуанцзян (霜降 — «Выпадение инея»)"),
        (281, "Сезон Ханьлу (寒露 — «Холодные росы»)"),
        (266, "Сезон Цюфэнь (秋分 — «Осеннее равноденствие»)"),
        (1, "Традиционный сезон китайского солнечного календаря (二十四节气)"),
    ]
    season_str = solar_terms[-1][1]
    for start_day, name in sorted(solar_terms, reverse=True):
        if doy >= start_day:
            season_str = name
            break

    cn_hol = cn_fixed.get((now.month, now.day)) or cn_wiki_hol or season_str
    if cn_fixed.get((now.month, now.day)) and season_str:
        cn_hol = f"{cn_hol} • {season_str}"

    return f"• 🇷🇺 <b>В России:</b> {ru_hol}\n• 🇨🇳 <b>В Китае:</b> {cn_hol}"


def get_horoscope():
    try:
        r = requests.get(
            "https://ignio.com/r/export/utf/xml/daily/com.xml", timeout=10
        )
        root = ET.fromstring(r.content)
        aquarius = root.find(".//aquarius/today").text.strip()
        scorpio = root.find(".//scorpio/today").text.strip()
        return (
            f"♒️ <b>Водолей:</b> {aquarius}\n\n♏️ <b>Скорпион:</b> {scorpio}"
        )
    except Exception as e:
        return f"Не удалось загрузить гороскоп ({e})"


def send_digest():
    send_morning_duck()
    today = datetime.now().strftime("%d.%m.%Y")
    text = (
        f"📊 <b>Сводка на {today}</b>\n\n"
        f"🏦 <b>Курсы валют:</b>\n{get_currencies_and_crypto()}\n\n"
        f"🌤 <b>Погода:</b>\n{get_weather()}\n\n"
        f"🎉 <b>Праздники сегодня:</b>\n{get_holidays()}\n\n"
        f"✨ <b>Гороскоп на сегодня:</b>\n{get_horoscope()}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    )
    print("Ответ Telegram (текст):", resp.status_code)


if __name__ == "__main__":
    send_digest()