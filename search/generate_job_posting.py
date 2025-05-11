import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import geopandas as gpd
from django.contrib.gis.geos import Point

from job_posting.models import JobPosting
from user.models import CompanyInfo

# 1. SHP 파일 경로 로드 및 좌표계 변환
shp_path = "search/logical_data/new_logical_data.shp"
gdf = gpd.read_file(shp_path).to_crs(epsg=5179)  # EPSG:5179 (GeoDjango default in Korea)

# 2. 행정구역 필드 이름 정의 (아래 필드 이름은 실제 SHP 필드명에 따라 조정 필요)
CITY_FIELD = "CITY_NAME"  # 시도
DISTRICT_FIELD = "DIST_NAME"  # 시군구
TOWN_FIELD = "EMD_NAME"  # 읍면동

# 3. 생성할 데이터 수
N = 1000

# 4. 직종, 교육, 요일, 급여 등 더미 값 목록
main_keywords = ["외식·음료"]
sub_keywords = [
    ["서빙"],
    ["바리스타"],
    ["제과제빵사"],
    ["레스토랑"],
    ["커피전문점"],
    ["패스트푸드점"],
    ["아이스크림·디저트"],
    ["도시락·반찬"],
    ["바(bar)"],
    ["주방장·조리사"],
    ["주방보조·설거지"],
]
educations = ["고졸", "대졸이상"]
work_days = [["월", "화", "수"], ["화", "목", "토"], ["월", "화", "수", "목", "금", "토", "일"]]
salary_types = ["월급", "시급", "연봉"]
posting_types = ["기업", "공공"]
employment_types = ["정규직", "비정규직"]
experiences = ["경력", "무관"]

co = CompanyInfo.objects.first()
# 5. 특정 회사 UUID (고정값)
COMPANY_ID: uuid.UUID | Any = co.company_id if co else None
company = CompanyInfo.objects.get(company_id=COMPANY_ID)


def run_dummy_job_posting():
    created = 0

    while created < N:
        polygon = gdf.sample(1).iloc[0]
        try:
            point = polygon.geometry.representative_point()  # 중심 근처 랜덤 포인트

            JobPosting.objects.create(
                job_posting_title=f"공고 {created+1}",
                address="대한민국 어디쯤",
                city=polygon[CITY_FIELD],
                district=polygon[DISTRICT_FIELD],
                town=polygon[TOWN_FIELD],
                location=Point(point.x, point.y, srid=5179),
                work_time_start=datetime.strptime("09:00", "%H:%M").time(),
                work_time_end=datetime.strptime("18:00", "%H:%M").time(),
                posting_type=random.choice(posting_types),
                employment_type=random.choice(employment_types),
                work_experience=random.choice(experiences),
                job_keyword_main=random.choice(main_keywords),
                job_keyword_sub=random.choice(sub_keywords),
                number_of_positions=random.randint(1, 10),
                company_id=company,
                education=random.choice(educations),
                deadline=datetime.today().date() + timedelta(days=random.randint(1, 30)),
                time_discussion=random.choice([True, False]),
                day_discussion=random.choice([True, False]),
                work_day=random.choice(work_days),
                salary_type=random.choice(salary_types),
                salary=random.randint(2000000, 5000000),
                summary="자동 생성된 공고입니다.",
                content="이것은 테스트용 공고입니다.",
            )
            created += 1

        except Exception as e:
            print(f"오류 발생: {e}")
    print(f"{created}개의 공고가 생성되었습니다.")


if __name__ == "__main__":
    try:
        run_dummy_job_posting()
        print("Created dummy jobposting data")
    except Exception as e:
        raise e
