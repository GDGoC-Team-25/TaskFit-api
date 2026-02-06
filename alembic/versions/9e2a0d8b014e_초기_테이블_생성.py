"""초기 테이블 생성

Revision ID: 9e2a0d8b014e
Revises:
Create Date: 2026-02-07 01:43:32.798734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e2a0d8b014e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """기존 테이블 정리 후 새 스키마 생성."""

    # 기존 public 스키마 테이블 정리 (이전 설계 잔여물)
    conn = op.get_bind()
    for table in ['messages', 'evaluation_results', 'threads', 'tasks',
                  'user_competencies', 'companies', 'users']:
        conn.execute(sa.text(f'DROP TABLE IF EXISTS public.{table} CASCADE'))

    # 기존 taskfit 스키마 테이블 정리 (이전 설계 잔여물)
    for table in ['messages', 'evaluation_results', 'threads', 'tasks',
                  'user_competencies', 'companies', 'users']:
        conn.execute(sa.text(f'DROP TABLE IF EXISTS taskfit.{table} CASCADE'))

    # 기존 alembic_version 정리
    conn.execute(sa.text('DROP TABLE IF EXISTS public.alembic_version CASCADE'))

    # === 새 테이블 생성 ===

    # users
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('google_id', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_image', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('email'),
        schema='taskfit'
    )

    # companies
    op.create_table('companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('tech_blog_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='taskfit'
    )

    # job_roles
    op.create_table('job_roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', 'name', name='uq_job_roles_category_name'),
        schema='taskfit'
    )

    # tasks
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('job_role_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False),
        sa.Column('answer_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tech_stack', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='taskfit'
    )
    op.create_index('ix_tasks_company_job', 'tasks', ['company_id', 'job_role_id'], schema='taskfit')

    # submissions
    op.create_table('submissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='taskfit'
    )
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'], schema='taskfit')
    op.create_index('ix_submissions_task_id', 'submissions', ['task_id'], schema='taskfit')

    # threads
    op.create_table('threads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('persona_name', sa.String(length=50), nullable=False),
        sa.Column('persona_department', sa.String(length=50), nullable=False),
        sa.Column('topic_tag', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='questioning'),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('asked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id'),
        schema='taskfit'
    )
    op.create_index('ix_threads_user_id', 'threads', ['user_id'], schema='taskfit')

    # messages
    op.create_table('messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='taskfit'
    )
    op.create_index('ix_messages_thread_id', 'messages', ['thread_id'], schema='taskfit')

    # evaluations
    op.create_table('evaluations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('score_label', sa.String(length=30), nullable=False),
        sa.Column('scores_detail', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ai_summary', sa.Text(), nullable=False),
        sa.Column('analysis_points', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id'),
        sa.UniqueConstraint('thread_id'),
        schema='taskfit'
    )

    # user_competencies
    op.create_table('user_competencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('job_role_id', sa.Integer(), nullable=False),
        sa.Column('avg_score', sa.Float(), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('weak_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'company_id', 'job_role_id', name='uq_user_competencies'),
        schema='taskfit'
    )


def downgrade() -> None:
    """모든 테이블 삭제."""
    op.drop_table('user_competencies', schema='taskfit')
    op.drop_table('evaluations', schema='taskfit')
    op.drop_index('ix_messages_thread_id', table_name='messages', schema='taskfit')
    op.drop_table('messages', schema='taskfit')
    op.drop_index('ix_threads_user_id', table_name='threads', schema='taskfit')
    op.drop_table('threads', schema='taskfit')
    op.drop_index('ix_submissions_task_id', table_name='submissions', schema='taskfit')
    op.drop_index('ix_submissions_user_id', table_name='submissions', schema='taskfit')
    op.drop_table('submissions', schema='taskfit')
    op.drop_index('ix_tasks_company_job', table_name='tasks', schema='taskfit')
    op.drop_table('tasks', schema='taskfit')
    op.drop_table('job_roles', schema='taskfit')
    op.drop_table('companies', schema='taskfit')
    op.drop_table('users', schema='taskfit')
