# ruff: noqa: E501
"""테스트 데이터 시드 스크립트.

실행: uv run python scripts/seed_data.py
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import close_db, get_db


async def seed():
    async for db in get_db():
        await _seed_all(db)
    await close_db()


async def _seed_all(db: AsyncSession):
    # 기존 데이터 삭제 (역순)
    for table in [
        "user_competencies",
        "evaluations",
        "messages",
        "threads",
        "submissions",
        "tasks",
        "job_roles",
        "companies",
        "users",
    ]:
        await db.execute(text(f"DELETE FROM taskfit.{table}"))
    await db.commit()

    now = datetime.now(timezone.utc)

    # ── Users (3명) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.users (id, google_id, email, name, bio, profile_image, created_at, updated_at)
            VALUES
                (1, 'google_001', 'user1@example.com', '김민수', '백엔드 개발자 지망생', NULL, :now, :now),
                (2, 'google_002', 'user2@example.com', '이지영', 'PM을 꿈꾸는 대학생', NULL, :now, :now),
                (3, 'google_003', 'user3@example.com', '박서준', 'UX 디자이너 지망생', NULL, :now, :now)
        """),
        {"now": now},
    )

    # ── Companies (5개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.companies (id, name, description, logo_url, tech_blog_url, created_at)
            VALUES
                (1, '토스', '금융을 혁신하는 핀테크 기업', NULL, 'https://toss.tech', :now),
                (2, '우아한형제들', '배달의민족을 운영하는 푸드테크 기업', NULL, 'https://techblog.woowahan.com', :now),
                (3, '카카오', '국민 메신저 카카오톡을 운영하는 IT 기업', NULL, 'https://tech.kakao.com/blog', :now),
                (4, '네이버', '대한민국 대표 포털 및 IT 플랫폼 기업', NULL, 'https://d2.naver.com/helloworld', :now),
                (5, '당근마켓', '지역 기반 중고거래 플랫폼', NULL, 'https://medium.com/daangn', :now)
        """),
        {"now": now},
    )

    # ── JobRoles (10개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.job_roles (id, category, name, description, created_at)
            VALUES
                (1, '개발', '백엔드 개발자', '서버 및 API 개발을 담당합니다', :now),
                (2, '개발', '프론트엔드 개발자', '웹 클라이언트 개발을 담당합니다', :now),
                (3, '개발', 'iOS 개발자', 'iOS 앱 개발을 담당합니다', :now),
                (4, '개발', 'Android 개발자', 'Android 앱 개발을 담당합니다', :now),
                (5, '개발', '데이터 엔지니어', '데이터 파이프라인 구축을 담당합니다', :now),
                (6, '개발', 'DevOps 엔지니어', '인프라 및 배포 자동화를 담당합니다', :now),
                (7, '기획', '서비스 기획자', '서비스 기획 및 요구사항 정의를 담당합니다', :now),
                (8, '기획', '프로젝트 매니저', '프로젝트 관리 및 일정 조율을 담당합니다', :now),
                (9, '디자인', 'UX 디자이너', '사용자 경험 설계를 담당합니다', :now),
                (10, '디자인', 'UI 디자이너', '사용자 인터페이스 디자인을 담당합니다', :now)
        """),
        {"now": now},
    )

    # ── Tasks (10개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.tasks
                (id, company_id, job_role_id, title, description, category, difficulty, estimated_minutes, answer_type, key_points, tech_stack, created_at)
            VALUES
                (1, 1, 1, '토스 결제 API 설계', '토스의 결제 시스템 REST API를 설계하세요. 결제 요청, 승인, 취소 흐름을 포함해야 합니다.',
                 '개발', '중', 60, 'text', '["API 설계 능력", "결제 도메인 이해", "에러 처리"]', '["REST API", "Python", "PostgreSQL"]', :now),
                (2, 1, 2, '토스 앱 메인 화면 리뉴얼', '토스 앱의 메인 화면을 리뉴얼하는 프론트엔드 구현 과제입니다.',
                 '개발', '상', 90, 'text', '["컴포넌트 설계", "상태 관리", "성능 최적화"]', '["React", "TypeScript", "Next.js"]', :now),
                (3, 2, 1, '배민 주문 시스템 설계', '배달의민족 주문 처리 시스템의 백엔드 아키텍처를 설계하세요.',
                 '개발', '상', 90, 'text', '["시스템 설계", "동시성 처리", "확장성"]', '["Java", "Spring Boot", "Kafka"]', :now),
                (4, 2, 7, '배민 신규 서비스 기획서', '배달의민족에서 새로운 구독 서비스를 기획하세요.',
                 '기획', '중', 60, 'text', '["시장 분석", "유저 니즈 파악", "비즈니스 모델"]', NULL, :now),
                (5, 3, 1, '카카오톡 채팅 서버 설계', '대규모 메시징 서버의 아키텍처를 설계하세요.',
                 '개발', '상', 120, 'text', '["분산 시스템", "메시지 큐", "실시간 처리"]', '["Kotlin", "gRPC", "Redis"]', :now),
                (6, 3, 9, '카카오 이모티콘 탭 UX 개선', '카카오톡 이모티콘 탭의 사용자 경험을 개선하세요.',
                 '디자인', '중', 45, 'text', '["사용성 분석", "인터랙션 디자인", "프로토타이핑"]', NULL, :now),
                (7, 4, 5, '네이버 검색 데이터 파이프라인', '네이버 검색 로그를 수집하고 분석하는 데이터 파이프라인을 설계하세요.',
                 '개발', '상', 90, 'text', '["데이터 모델링", "ETL 설계", "스케일링"]', '["Apache Spark", "Airflow", "BigQuery"]', :now),
                (8, 4, 2, '네이버 지도 웹 성능 최적화', '네이버 지도 웹 버전의 로딩 속도를 개선하세요.',
                 '개발', '중', 60, 'text', '["웹 성능", "번들 최적화", "캐싱 전략"]', '["JavaScript", "Webpack", "Service Worker"]', :now),
                (9, 5, 3, '당근마켓 iOS 채팅 기능', '당근마켓 iOS 앱에 실시간 채팅 기능을 구현하세요.',
                 '개발', '중', 75, 'text', '["iOS 아키텍처", "실시간 통신", "UI 구현"]', '["Swift", "WebSocket", "UIKit"]', :now),
                (10, 5, 8, '당근마켓 지역 확장 프로젝트 관리', '당근마켓의 신규 지역 서비스 런칭 프로젝트를 관리하세요.',
                 '기획', '하', 30, 'text', '["일정 관리", "리스크 관리", "이해관계자 소통"]', NULL, :now)
        """),
        {"now": now},
    )

    # ── Submissions (3개) ──
    sub_time1 = now - timedelta(hours=2)
    sub_time2 = now - timedelta(hours=1)
    await db.execute(
        text("""
            INSERT INTO taskfit.submissions
                (id, user_id, task_id, content, is_draft, status, time_spent_seconds, created_at, updated_at)
            VALUES
                (1, 1, 1, '임시 저장 중인 결제 API 설계 초안입니다.', true, 'draft', 1200, :t1, :t1),
                (2, 1, 3, '배민 주문 시스템은 이벤트 기반 아키텍처로 설계합니다. 주문 생성, 결제, 배달 단계를 분리하고 Kafka로 이벤트를 전달합니다.', false, 'submitted', 3600, :t2, :t2),
                (3, 1, 5, '카카오톡 채팅 서버는 WebSocket 기반으로 구현하며, Redis Pub/Sub으로 서버 간 메시지를 전달합니다.', false, 'evaluated', 5400, :t2, :t2)
        """),
        {"t1": sub_time1, "t2": sub_time2},
    )

    # ── Threads (2개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.threads
                (id, submission_id, user_id, persona_name, persona_department, topic_tag, status, total_questions, asked_count, created_at, updated_at)
            VALUES
                (1, 2, 1, '이상현', '주문개발팀', '시스템 설계', 'questioning', 3, 1, :t, :t),
                (2, 3, 1, '정우진', '메시징플랫폼팀', '분산 시스템', 'completed', 3, 3, :t, :t)
        """),
        {"t": sub_time2},
    )

    # ── Messages ──
    await db.execute(
        text("""
            INSERT INTO taskfit.messages (id, thread_id, role, content, message_order, created_at)
            VALUES
                (1, 1, 'ai', '주문 시스템에서 이벤트 기반 아키텍처를 선택한 이유가 무엇인가요? 동기 방식과 비교했을 때 어떤 장점이 있다고 생각하시나요?', 1, :t),
                (2, 2, 'ai', 'WebSocket과 Redis Pub/Sub을 조합한 이유를 설명해주세요. 다른 대안은 고려하지 않으셨나요?', 1, :t),
                (3, 2, 'user', 'HTTP 폴링이나 SSE도 고려했지만, 실시간 양방향 통신이 필요한 채팅 특성상 WebSocket이 가장 적합하다고 판단했습니다.', 2, :t),
                (4, 2, 'ai', '서버가 수평 확장될 때 WebSocket 세션 관리는 어떻게 처리하실 건가요?', 3, :t),
                (5, 2, 'user', 'Redis Pub/Sub으로 서버 간 메시지를 브로드캐스트하고, 각 서버는 자신이 관리하는 WebSocket 연결에만 메시지를 전달합니다.', 4, :t),
                (6, 2, 'ai', '대규모 트래픽 상황에서 Redis Pub/Sub의 한계점은 무엇이며, 이를 어떻게 해결하시겠습니까?', 5, :t),
                (7, 2, 'user', 'Redis Pub/Sub은 메시지 지속성이 없어 서버 장애 시 메시지 유실 가능성이 있습니다. 이를 위해 Redis Streams나 Kafka를 보조로 사용하여 메시지 내구성을 보장할 수 있습니다.', 6, :t)
        """),
        {"t": sub_time2},
    )

    # ── Evaluations (1개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.evaluations
                (id, submission_id, thread_id, total_score, score_label, scores_detail, ai_summary, analysis_points, feedback, created_at)
            VALUES (
                1, 3, 2, 78, 'B',
                '[{"name": "문제 이해도", "score": 82}, {"name": "실무 적합성", "score": 75}, {"name": "논리적 사고", "score": 80}, {"name": "커뮤니케이션", "score": 74}]',
                '분산 메시징 시스템에 대한 기본적인 이해를 바탕으로 합리적인 아키텍처를 제시했습니다. 특히 Redis Pub/Sub의 한계를 인지하고 대안을 제시한 점이 좋았습니다.',
                '{"strengths": ["분산 시스템 기본 개념 이해", "대안 기술 제시 능력"], "weaknesses": ["구체적인 구현 계획 부족", "장애 복구 시나리오 미흡"]}',
                '실제 프로덕션 환경에서의 장애 복구 시나리오와 모니터링 방안까지 고려하면 더 완성도 높은 설계가 될 것입니다.',
                :t
            )
        """),
        {"t": sub_time2},
    )

    # ── UserCompetencies (2개) ──
    await db.execute(
        text("""
            INSERT INTO taskfit.user_competencies
                (id, user_id, company_id, job_role_id, avg_score, attempt_count, weak_tags, updated_at)
            VALUES
                (1, 1, 3, 1, 78.0, 1, '["구체적인 구현 계획 부족", "장애 복구 시나리오 미흡"]', :t),
                (2, 1, 2, 1, 0.0, 1, NULL, :t)
        """),
        {"t": now},
    )

    # 시퀀스 리셋
    for table, seq_val in [
        ("users", 4),
        ("companies", 6),
        ("job_roles", 11),
        ("tasks", 11),
        ("submissions", 4),
        ("threads", 3),
        ("messages", 8),
        ("evaluations", 2),
        ("user_competencies", 3),
    ]:
        await db.execute(
            text(f"SELECT setval(pg_get_serial_sequence('taskfit.{table}', 'id'), {seq_val}, false)")
        )

    await db.commit()
    print("시드 데이터 삽입 완료!")


if __name__ == "__main__":
    asyncio.run(seed())
