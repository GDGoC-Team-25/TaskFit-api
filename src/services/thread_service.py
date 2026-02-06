from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database.message import Message
from src.models.database.thread import Thread


async def create_thread_with_first_message(
    db: AsyncSession,
    *,
    submission_id: int,
    user_id: int,
    persona_name: str,
    persona_department: str,
    topic_tag: str,
    total_questions: int,
    first_message_content: str,
) -> tuple[Thread, Message]:
    thread = Thread(
        submission_id=submission_id,
        user_id=user_id,
        persona_name=persona_name,
        persona_department=persona_department,
        topic_tag=topic_tag,
        total_questions=total_questions,
        asked_count=1,
    )
    db.add(thread)
    await db.flush()

    message = Message(
        thread_id=thread.id,
        role="ai",
        content=first_message_content,
        message_order=1,
    )
    db.add(message)
    await db.commit()
    await db.refresh(thread)
    await db.refresh(message)
    return thread, message


async def get_threads(
    db: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Thread], int]:
    count_stmt = select(func.count(Thread.id)).where(Thread.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    stmt = (
        select(Thread)
        .where(Thread.user_id == user_id)
        .order_by(Thread.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def get_thread_detail(db: AsyncSession, thread_id: int) -> Thread | None:
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    return result.scalar_one_or_none()


async def get_thread_messages(db: AsyncSession, thread_id: int) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.message_order)
    )
    return list(result.scalars().all())


async def add_user_message(
    db: AsyncSession, thread_id: int, content: str, message_order: int
) -> Message:
    message = Message(
        thread_id=thread_id,
        role="user",
        content=content,
        message_order=message_order,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def add_ai_message(
    db: AsyncSession, thread_id: int, content: str, message_order: int
) -> Message:
    message = Message(
        thread_id=thread_id,
        role="ai",
        content=content,
        message_order=message_order,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def complete_thread(db: AsyncSession, thread: Thread) -> Thread:
    thread.status = "completed"
    await db.commit()
    await db.refresh(thread)
    return thread


async def increment_asked_count(db: AsyncSession, thread: Thread) -> Thread:
    thread.asked_count += 1
    await db.commit()
    await db.refresh(thread)
    return thread


async def get_thread_by_submission_id(
    db: AsyncSession, submission_id: int
) -> Thread | None:
    result = await db.execute(
        select(Thread).where(Thread.submission_id == submission_id)
    )
    return result.scalar_one_or_none()
