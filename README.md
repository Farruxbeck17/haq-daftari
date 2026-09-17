# Haq daftari

O'zbekistonda o'zaro qarzlarni qayd etish, ikki tomonlama tasdiqlash, qisman to'lovlar va muloyim eslatmalar uchun Telegram mini ilovasi.

Server: Python 3.11, FastAPI, SQLAlchemy 2.0, asyncpg, PostgreSQL, Aiogram 3 va APScheduler. Interfeys: React, TypeScript, Vite va Tailwind CSS. Pul qiymatlari bazada aniq o'nlik sonlar sifatida saqlanadi. Hozircha faqat UZS qabul qilinadi.

## Ishga tushirish

1. BotFather orqali bot yarating. Bot tokeni va foydalanuvchi nomini oling. Mini ilova uchun HTTPS manzili kerak.
2. Python 3.11, Node.js 22 va Docker Compose o'rnating.
3. Loyiha ildizida sozlash dasturini ishga tushiring:

```sh
python scripts/configure.py
docker compose up --build -d
docker compose logs -f backend
```

Sozlash dasturi token va manzillarni so'raydi, JWT kaliti va baza parolini yaratadi. Maxfiy qiymatlar Git tarkibiga kiritilmaydi. `.env.example` ichidagi bo'sh qiymatlar operator kiritadigan haqiqiy hisob ma'lumotlari uchun; dasturda yashirin sinov akkaunti yoki kirishni chetlab o'tish yo'li yo'q.

Compose PostgreSQL portini tashqariga chiqarmaydi. Server faqat `127.0.0.1:8000` orqali ochiladi. Alohida HTTPS teskari proksi yoki mahalliy HTTPS tunnel kerak. Proksida so'rov hajmini 32 KB bilan, kirish tezligini esa tegishli foydalanuvchi/IP chegaralari bilan cheklang. So'rov sarlavhalari, JWT va Telegram initData qiymatlarini jurnalga yozmang.

Compose har ishga tushishda `alembic upgrade head` bajaradi. Ma'lumotlar `postgres_data` jildida saqlanadi. `docker compose down` ma'lumotlarni saqlaydi; `down -v` ma'lumotlarni o'chiradi.

## Interfeysni mahalliy ishga tushirish

```sh
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Vite manzili `http://127.0.0.1:5173`. API so'rovlari odatda Vite proksisi orqali mahalliy serverga o'tadi. Telegram orqali ishlatish uchun Vite manziliga HTTPS tunnel o'rnating, `WEBAPP_URL` va `CORS_ORIGINS` qiymatlarini uning manziliga moslang va serverni qayta ishga tushiring. Tunnel xizmati talab qilsa, Vite `server.allowedHosts` ro'yxatiga faqat o'zingizning tunnel domeningizni qo'shing.

Oddiy brauzerda tizim Telegram orqali ochishni so'raydi. Haqiqiy hisob ma'lumotlari o'rniga sun'iy foydalanuvchi yaratilmaydi. Ish stoli Telegram dasturi orqali ham sinash mumkin.

## Vercel va ishchi server

Vercel loyihasida asosiy jildni `frontend`, yig'ish buyrug'ini `pnpm build`, natija jildini `dist` qilib belgilang. Quyidagi muhit qiymatlarini kiriting:

- `VITE_API_URL`: FastAPI serverining HTTPS manzili, oxirida `/api/v1` bo'lmasin.
- `VITE_BOT_USERNAME`: BotFather bergan bot nomi, `@` belgisiz.

Serverdagi `WEBAPP_URL` Vercel ilovasining HTTPS manziliga teng bo'lsin. `CORS_ORIGINS` shu manzilni o'z ichiga olgan JSON ro'yxat bo'lsin. `ENVIRONMENT=production` va `AUTO_CREATE_TABLES=false` belgilang. Sozlash dasturi ishchi muhitni tanlash imkonini beradi. Vercel faqat interfeysni joylashtiradi; PostgreSQL, bot polling va rejalashtiruvchi doimiy ishlaydigan serverda qoladi.

BotFather ichida `/setmenubutton` orqali mini ilova manzilini kiriting. Botga shaxsiy xabarda `/start` yuboring va «Daftarni ochish» tugmasini bosing. Telegram mini ilovalari HTTPS talab qiladi.

Standart joylashtirishda bitta Uvicorn jarayoni ishlaydi. Qo'shimcha API nusxalarida `RUN_BOT=false` va `RUN_SCHEDULER=false` bo'lishi kerak. Bot/rejalashtiruvchi nusxasi PostgreSQL maslahat qulfini egallaydi; ikkinchi nusxa ishga tushmaydi. Polling uchun webhook o'chiriladi, lekin kutilayotgan yangilanishlar tashlab yuborilmaydi.

`GET /health` baza aloqasini va polling vazifasining holatini tekshiradi. Jarayon nosozligini kuzatuvchi tizimni sozlang. Ishchi muhitda Swagger sahifasi yopiq.

## Hisob-kitob qoidalari

- «Men berdim» yozuvida muallif haqdor. «Men oldim» yozuvida muallif qarzdor.
- Tasdiqlangan ikkinchi tomon yozuvni teskari yo'nalishda ko'radi. Baza foydalanuvchi ID qiymati Telegram ID qiymatidan alohida saqlanadi.
- Tasdiq kutilayotgan va rad etilgan yozuvlar umumiy balansga qo'shilmaydi.
- Ulashilgan yozuvda to'lovni faqat haqdor qayd etadi. Yakka daftardagi yozuvni uning muallifi boshqaradi.
- To'lov pul o'tkazmaydi: u avval bajarilgan hisob-kitobni qayd etadi.
- To'lov bazadagi qator qulfi bilan bajariladi. Qoldiqdan katta yoki manfiy to'lov qabul qilinmaydi.
- Har bir to'lov uchun UUID `idempotency_key` majburiy. Xuddi shu kalit va mazmun bilan qayta so'rov bir to'lovni takrorlamaydi. Kalit boshqa mazmun bilan qayta ishlatilsa, 409 javobi qaytadi.
- Qisman to'lov `PARTIALLY_PAID`, nol qoldiq `SETTLED` holatiga o'tadi.
- «Kutilayotgan» bo'limi bugun yoki kelajakda muddati keladigan ochiq qarzlarni ko'rsatadi. Sana belgilanmagan va tasdiq kutilayotgan yozuvlar «Barchasi» bo'limida.
- Ro'yxat `limit` va `offset` bilan sahifalanadi. Interfeys «Yana ko'rsatish» tugmasidan foydalanadi.
- Tasdiqlash havolasi maxfiy taklif vazifasini bajaradi. Uni olgan birinchi boshqa foydalanuvchi tasdiqlashi yoki rad etishi mumkin. Telefon raqami havola oluvchisining shaxsini isbotlamaydi. Havolani faqat tegishli kishiga shaxsiy tarzda yuboring.
- Tasdiqlash va rad etish qator qulfi bilan bir marta bajariladi. Muallif o'z yozuvini tasdiqlay olmaydi. Yangi foydalanuvchi bazaga qo'shiladi va uning ichki ID qiymati qarzga bog'lanadi.

## Eslatmalar va Eskiz

Rejalashtiruvchi har kuni Toshkent vaqti bilan 09:00 da ishga tushadi. Muddati uch kundan keyin, bugun yoki o'tgan ochiq qarzlar ko'rib chiqiladi. Qo'lda yuborish va kundalik vazifa bitta 24 soatlik cheklovdan foydalanadi.

Xabar haqiqiy qarzdorga yuboriladi: GIVEN yozuvida ikkinchi tomonga, TAKEN yozuvida muallifga. Bog'langan Telegram foydalanuvchisi bo'lmasa, GIVEN yozuvi uchun ko'rsatilgan telefon raqamiga SMS yuboriladi. Bot bloklangan bo'lsa, yashirin ravishda boshqa kanalga o'tilmaydi.

Eskiz uchun `ESKIZ_EMAIL`, `ESKIZ_PASSWORD` va tasdiqlangan `ESKIZ_SENDER` qiymatlarini kiriting. Eskiz hisobingizda yuboriladigan matn shakllari va jo'natuvchi tasdiqlangan bo'lishi kerak. Haqiqiy SMS uchun foydalanuvchining `sms_balance` qiymati musbat bo'lishi kerak. Ushbu loyiha SMS paketlarini sotish yoki onlayn to'lov xizmatini o'z ichiga olmaydi; vakolatli operator balansni bazada boshqaradi.

Email kiritilmagan rivojlantirish muhitida SMS konsolga sinov xabari sifatida yoziladi, javobda `mock_sms` kanali qaytadi va balans kamaymaydi. Ishchi muhitda bu holat 503 xatosini qaytaradi.

Yuborishdan **avval** eslatma vaqti va SMS sarfi bazaga yoziladi. Bu xizmat javobi yo'qolganida yoki jarayon qayta ishga tushganida takroriy xabar yuborishni kamaytiradi. Xizmatga topshirish yetkazib berilganini anglatmaydi. Noaniq yoki xato javobda cheklov va SMS sarfi avtomatik qaytarilmaydi; operator Eskiz hisobotini tekshirib hisobni tuzatishi mumkin. Jarayon saqlash va yuborish oralig'ida to'xtasa, xabar yo'qolishi mumkin. Bu ataylab tanlangan eng ko'pi bilan bir marta urinish tartibi; kafolatlangan yetkazib berish uchun alohida navbat va yetkazib berish holatlari kerak.

## Sinovlar

```sh
cd backend
python -m venv .venv
```

Linux/macOS:

```sh
. .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

```sh
pip install -r requirements-dev.txt
pytest -q
```

PostgreSQL sinovlari alohida bazani talab qiladi. Ular test bazasida loyiha jadvallarini yaratadi va o'chiradi; jonli bazaga ulamang. Baza nomi `_test` bilan tugashi tekshiriladi.

Ishchi Docker tasvirida testlar va pytest yo'q. To'liq ajratilgan tekshiruv uchun quyidagi buyruqdan foydalaning:

```sh
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
docker compose -f docker-compose.test.yml down -v
```

Oddiy pytest ishga tushirilganda `TEST_DATABASE_URL` berilmasa, PostgreSQL sinovlari o'tkazib yuboriladi. Unit sinovlari tashqi xabar yubormaydi; Telegram jo'natuvchisi almashtiriladi. Baza sinovlari kirish huquqlari, balanslar, takroriy so'rov va parallel to'lovlarni qamrab oladi.

Interfeys:

```sh
cd frontend
pnpm build
```

Ayrim cheklangan Windows muhitlarida Vite konfiguratsiyasini yig'uvchi esbuild yuqori jildlarni o'qiy olmaydi. Bunday muhit uchun muqobil tekshiruv:

```sh
pnpm exec tsc --noEmit
pnpm exec vite build --configLoader runner
```

## Xavfsizlik va xizmat ko'rsatish

Telegram initData HMAC-SHA256 bilan tekshiriladi, imzo doimiy vaqtli solishtirish orqali solishtiriladi. Bir soatdan eski va kelajakdagi noto'g'ri kirishlar rad etiladi. HMAC uchun barcha qabul qilingan maydonlar, `hash` bundan mustasno, tekshiruv satriga kiradi. JWT faqat HS256, belgilangan issuer va audience bilan qabul qilinadi.

JWT topshiriq talabiga ko'ra localStorage ichida saqlanadi. Brauzerdagi XSS tokenni o'g'irlashi mumkin; tashqi skriptlarni kiritmang, frontendni HTTPS orqali bering va bog'liqliklarni kuzating. Telegram foydalanuvchisining tekshirilmagan frontend ma'lumotlari kirishga ruxsat berish uchun ishlatilmaydi.

Asosiy Python kutubxona talqinlari topshiriqdagi aniq ro'yxatga mos saqlandi. Bu tarixiy talqinlar avtomatik ravishda xavfsiz yoki bugungi ishchi muhit uchun sertifikatlangan degani emas. Ishga chiqarishdan oldin bog'liqlik auditi, zarur yangilanishlar, zaxira nusxa va tiklash sinovi, tashqi xizmatlar bilan haqiqiy yakuniy sinovni bajaring. PostgreSQL va Python tasvirlariga xavfsizlik yangilanishlarini qo'llang.

Baza sxemasi o'zgarsa, Alembic migratsiyasini yarating va ko'rib chiqing. `create_all` mavjud jadvallardagi ustunlarni yangilamaydi. Ishchi muhitda migratsiya talab qilinadi.

Ma'lumotlarni zaxiralash uchun `pg_dump`, tiklash uchun mos `pg_restore` ish jarayonini sozlang. Telefon va qarz yozuvlariga faqat vakolatli operatorlar kira olsin.

## Asosiy manbalar

- [Telegram mini ilovalarida ma'lumotni tekshirish](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- [SQLAlchemy asinxron sessiyalari](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Aiogram hujjatlari](https://docs.aiogram.dev/en/v3.10.0/)
- [Eskiz jo'natuvchi kabineti](https://my.eskiz.uz/)
