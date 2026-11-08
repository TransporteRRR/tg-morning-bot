from datetime import datetime
import os
import random
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests


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

WEEKDAYS = {
    0: ("Доброе утро! Отличного понедельника!", "早上好！祝你星期一愉快！"),
    1: ("Доброе утро! Прекрасного вторника!", "早上好！祝你星期二愉快！"),
    2: ("Доброе утро! Удачной среды!", "早上好！祝你星期三愉快！"),
    3: ("Доброе утро! Хорошего четверга!", "早上好！祝你星期四愉快！"),
    4: ("Доброе утро! С пятницей!", "早上好！祝你星期五愉快！"),
    5: ("Доброе утро! Чудесной субботы!", "早上好！祝你星期六愉快！"),
    6: ("Доброе утро! Прекрасного воскресенья!", "早上好！祝你星期日愉快！"),
}

DUCK_STYLES = [
    (
        "3D Pixar animation",
        "cute fluffy 3D Pixar style duck waving wing happily, warm morning sunlight, coffee cup, 8k render",
    ),
    (
        "Фото National Geographic",
        "award winning National Geographic wildlife macro photo of a real cute duck waving its wing in golden morning mist by a lake",
    ),
    (
        "Аниме Studio Ghibli",
        "cozy Studio Ghibli anime illustration of a cute duck waving good morning on a sunny balcony with tea",
    ),
    (
        "Китайская живопись (Ханчжоу)",
        "traditional Chinese ink and watercolor painting of a cute duck waving wing at sunrise over West Lake in Hangzhou with pagodas",
    ),
    (
        "Киберпанк",
        "cool cute cyberpunk duck wearing neon visor waving wing in a futuristic sunny morning city, vibrant colors",
    ),
    (
        "Вязаная игрушка (Амигуруми)",
        "macro photo of a cute handmade knitted crochet amigurumi duck toy waving wing on a cozy wooden breakfast table",
    ),
    (
        "Акварельная открытка",
        "delicate artistic watercolor painting of a cheerful duck waving wing among morning flowers, bright sunny mood",
    ),
    (
        "Стиль LEGO",
        "cute LEGO brick duck figure waving wing in a sunny LEGO morning garden, macro photography",
    ),
]


def send_morning_duck():
    ru_greet, cn_greet = WEEKDAYS[datetime.now().weekday()]
    style_name, style_prompt = random.choice(DUCK_STYLES)
    seed = random.randint(1, 999999)

    encoded_prompt = urllib.parse.quote(style_prompt)
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true"
    caption = f"🦆 <b>{ru_greet}</b>\n🇨🇳 <b>{cn_greet}</b>\n\n<i>🎨 Стиль дня: {style_name}</i>"
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    try:
        print("Генерирую утку через ИИ (около 5-10 сек)...")
        img_resp = requests.get(img_url, timeout=45)
        if img_resp.status_code == 200:
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
            )
    except Exception as e:
        print("Ошибка отправки утки:", e)


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
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*°C", html)
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


def get_holidays():
    today_str = datetime.now().strftime("%d.%m")
    prompt = (
        f"Сегодня дата {today_str}. Напиши строго в 2 короткие строки без вступлений и кавычек:\n"
        f"• 🇷🇺 В России: (главный государственный, профессиональный или народный праздник России на {today_str})\n"
        f"• 🇨🇳 В Китае: (какой сегодня праздник, памятный день или сезон в Китае на {today_str})"
    )
    try:
        r = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "openai",
            },
            timeout=15,
        )
        if r.status_code == 200 and len(r.text.strip()) > 10:
            return r.text.strip()
    except Exception as e:
        return f"Не удалось загрузить праздники ({e})"
    return "Нет данных о праздниках"


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