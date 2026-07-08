# Recipe App — Backend

REST API для мобильного приложения по поиску и адаптации рецептов питания.

## Стек

- **Python 3.10** + **FastAPI**
- **PostgreSQL** (Docker)
- **SQLAlchemy** + **Alembic**
- **Spoonacular API** — база рецептов
- **Claude AI (Anthropic)** — замена ингредиентов
- **JWT** — авторизация

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/твой_юзер/recipe_app.git
cd recipe_app
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
```

Заполни `.env`:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5444/recipe_app
SECRET_KEY=  # python -c "import secrets; print(secrets.token_hex(32))"
ANTHROPIC_API_KEY=  # console.anthropic.com
SPOONACULAR_API_KEY=  # spoonacular.com/food-api
UNSPLASH_ACCESS_KEY=  # unsplash.com/oauth/applications
```

### 5. Запустить базу данных

```bash
docker-compose up -d
```

### 6. Применить миграции

```bash
alembic upgrade head
```

### 7. Запустить сервер

```bash
uvicorn main:app --reload
```

Документация: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Эндпоинты

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/v1/auth/register` | Регистрация |
| POST | `/v1/auth/login` | Логин |
| GET | `/v1/auth/me` | Профиль пользователя |
| PATCH | `/v1/auth/me/profile` | Обновить профиль |

### Рецепты
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/v1/recipes/search?ingredients=chicken,rice` | Поиск рецептов |
| GET | `/v1/recipes/{id}` | Детали рецепта |
| GET | `/v1/recipes/daily` | Рецепт дня |
| GET | `/v1/recipes/saved` | Избранные рецепты |
| POST | `/v1/recipes/{id}/save` | Сохранить рецепт |
| DELETE | `/v1/recipes/{id}/save` | Удалить из избранного |
| POST | `/v1/recipes/scale` | Пересчёт порций |
| POST | `/v1/recipes/substitute` | Замена ингредиента (AI) |
| GET | `/v1/recipes/history` | История поиска |
| GET | `/v1/recipes/popular-ingredients` | Популярные ингредиенты |

### Прочее
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/health` | Health check |

---

## Поиск с граммовками

Можно передавать количество прямо в строке поиска:

```
/v1/recipes/search?ingredients=chicken 250g,rice 150g,eggs 3
```

Все ингредиенты и КБЖУ пересчитаются под указанные количества.

---

## Для разработки

Открыть доступ для других устройств через ngrok:

```bash
ngrok http 8000
```