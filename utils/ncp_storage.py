import os
import uuid
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings


# secrets.json에서 인증 정보를 로드
def load_secrets():
    secrets_path = os.path.join(settings.BASE_DIR, 'secrets.json')  # secrets.json 경로
    try:
        with open(secrets_path, 'r') as f:
            secrets = json.load(f)
        return secrets
    except Exception as e:
        raise Exception(f"secrets.json 파일을 로드하는데 실패했습니다: {e}")


# NCP S3에 파일 업로드
def upload_to_ncp_storage(file_obj):
    secrets = load_secrets()  # secrets.json에서 인증 정보 가져오기

    # 인증키 설정
    ACCESS_KEY = secrets["NCP_S3_ACCESS_KEY"]
    SECRET_KEY = secrets["NCP_S3_SECRET_KEY"]
    REGION = secrets["NCP_S3_REGION_NAME"]
    ENDPOINT_URL = secrets["NCP_S3_ENDPOINT"]
    BUCKET_NAME = secrets["NCP_S3_BUCKET_NAME"]

    # 확장자 추출 (예: ".jpg", ".png")
    ext = os.path.splitext(file_obj.name)[1]

    # 유효한 확장자만 허용
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if ext.lower() not in valid_extensions:
        raise ValueError("지원하지 않는 파일 형식입니다.")

    # UUID + 확장자 조합으로 고유한 파일명 생성
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    # 업로드할 경로 지정 (폴더 구조 가능)
    s3_key = f"uploads/{unique_filename}"

    # S3 클라이언트 생성
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
    )

    try:
        # 파일 업로드
        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={
                "ContentType": file_obj.content_type,
                # "ACL": "public-read",  # 파일을 공개적으로 접근할 수 있도록 설정
            },
        )

        # 업로드된 파일의 전체 URL 생성
        file_url = f"{ENDPOINT_URL}/{BUCKET_NAME}/{s3_key}"

        # 업로드 성공 로그
        print(f"파일 업로드 성공, URL: {file_url}")

        return file_url

    except (BotoCoreError, ClientError) as e:
        raise Exception(f"파일 업로드 실패: {e}")
    except ValueError as ve:
        raise Exception(f"파일 검증 실패: {ve}")


"""
def upload_view(request):  #이미지 업로드 메서드
    if request.method == "POST":
        if 'file' not in request.FILES:
            return JsonResponse({'error': '파일이 없습니다.'}, status=400)

        file_obj = request.FILES['file']

        try:
            file_url = upload_to_ncp_storage(file_obj) # 실제 스토리지에 저장된 파일 url

            return JsonResponse({'file_url': file_url})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

"""
