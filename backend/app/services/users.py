from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def upsert_user(db: AsyncSession, data: dict) -> User:
    values = dict(telegram_id=data["id"], first_name=data["first_name"],
                  last_name=data.get("last_name"), username=data.get("username"))
    statement = insert(User).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[User.telegram_id],
        set_={key: value for key, value in values.items() if key != "telegram_id"},
    ).returning(User)
    return (await db.execute(statement, execution_options={"populate_existing": True})).scalar_one()
