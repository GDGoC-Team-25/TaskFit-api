import json

from google import genai

from src.core.config import get_settings


def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


MODEL = "gemini-3.0-flash-preview"


async def generate_tasks(
    company_name: str,
    job_role_name: str,
    count: int = 5,
) -> list[dict]:
    """AI로 실무 과제를 생성한다."""
    client = _get_client()

    prompt = f"""당신은 기업 실무 과제를 만드는 전문가입니다.

다음 조건에 맞는 실무 과제 {count}개를 생성해주세요:
- 기업: {company_name}
- 직무: {job_role_name}

각 과제는 실제 해당 기업의 해당 직무에서 수행할 법한 실무 과제여야 합니다.

JSON 배열로 응답해주세요. 각 항목:
{{
  "title": "과제 제목",
  "description": "과제 상세 설명 (3-5문장)",
  "category": "과제 카테고리 (예: 기획, 개발, 분석, 디자인)",
  "difficulty": "상/중/하 중 하나",
  "estimated_minutes": 예상 소요 시간(분, 정수),
  "answer_type": "text",
  "key_points": ["핵심 평가 포인트1", "핵심 평가 포인트2", "핵심 평가 포인트3"],
  "tech_stack": ["관련 기술1", "관련 기술2"]
}}"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


async def generate_persona(
    company_name: str,
    job_role_name: str,
    task_title: str,
) -> dict:
    """AI 상사 페르소나를 생성한다."""
    client = _get_client()

    prompt = f"""당신은 면접관 페르소나를 만드는 전문가입니다.

다음 상황에 맞는 면접관 페르소나를 생성해주세요:
- 기업: {company_name}
- 직무: {job_role_name}
- 과제: {task_title}

면접관은 해당 기업의 실무 담당자(팀장급)로, 제출된 과제에 대해 의도와 이해도를 파악하는 질의응답을 진행합니다.

JSON으로 응답해주세요:
{{
  "persona_name": "면접관 이름 (한국어, 예: 김민수)",
  "persona_department": "소속 부서 (예: 프론트엔드 개발팀)",
  "topic_tag": "질의 주제 태그 (예: 기술 설계)",
  "total_questions": 질문 수(3~5 사이 정수)
}}"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


async def generate_first_question(
    company_name: str,
    job_role_name: str,
    task_title: str,
    task_description: str,
    submission_content: str,
    persona_name: str,
    persona_department: str,
) -> str:
    """첫 번째 질문을 생성한다."""
    client = _get_client()

    prompt = f"""당신은 {company_name}의 {persona_department} 소속 {persona_name}입니다.

지원자가 다음 과제를 제출했습니다:
- 과제: {task_title}
- 과제 설명: {task_description}
- 제출 내용: {submission_content}

제출물을 검토한 후, 지원자의 의도와 이해도를 파악하기 위한 첫 번째 질문을 해주세요.
질문은 구체적이고 실무적이어야 합니다. 질문만 작성해주세요."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text


async def generate_follow_up(
    company_name: str,
    job_role_name: str,
    task_title: str,
    task_description: str,
    submission_content: str,
    persona_name: str,
    persona_department: str,
    conversation_history: list[dict],
    question_number: int,
    total_questions: int,
) -> str:
    """후속 질문을 생성한다."""
    client = _get_client()

    history_text = "\n".join(
        f"{'면접관' if m['role'] == 'ai' else '지원자'}: {m['content']}"
        for m in conversation_history
    )

    prompt = f"""당신은 {company_name}의 {persona_department} 소속 {persona_name}입니다.

과제: {task_title}
과제 설명: {task_description}
지원자 제출물: {submission_content}

지금까지의 대화:
{history_text}

이것은 {total_questions}개 질문 중 {question_number}번째 질문입니다.
이전 대화를 바탕으로 지원자의 이해도를 더 깊이 파악할 수 있는 후속 질문을 해주세요.
질문만 작성해주세요."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text


async def evaluate_submission(
    company_name: str,
    job_role_name: str,
    task_title: str,
    task_description: str,
    key_points: list[str] | None,
    submission_content: str,
    conversation_history: list[dict],
) -> dict:
    """제출물과 질의응답을 기반으로 채점한다."""
    client = _get_client()

    history_text = "\n".join(
        f"{'면접관' if m['role'] == 'ai' else '지원자'}: {m['content']}"
        for m in conversation_history
    )

    key_points_text = ", ".join(key_points) if key_points else "없음"

    prompt = f"""당신은 채점 전문가입니다. 다음 과제 제출물과 질의응답을 기반으로 채점해주세요.

기업: {company_name}
직무: {job_role_name}
과제: {task_title}
과제 설명: {task_description}
핵심 평가 포인트: {key_points_text}

제출물:
{submission_content}

질의응답:
{history_text}

다음 JSON 형식으로 채점해주세요:
{{
  "total_score": 총점(0-100),
  "score_label": "등급 (S/A/B/C/D 중 하나)",
  "scores_detail": [
    {{"name": "문제 이해도", "score": 점수(0-100)}},
    {{"name": "실무 적합성", "score": 점수(0-100)}},
    {{"name": "논리적 사고", "score": 점수(0-100)}},
    {{"name": "커뮤니케이션", "score": 점수(0-100)}}
  ],
  "ai_summary": "전반적인 평가 요약 (2-3문장)",
  "analysis_points": {{
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1", "약점2"]
  }},
  "feedback": "구체적인 피드백 및 개선 방향 (2-3문장)"
}}"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)
