# ------------------------
# serializer (추후 분리 예정)
# ------------------------
from typing import List

from resume.models import CareerInfo, Certification, Submission
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    JobpostingListOutputModel,
    SubmissionModel,
)


def serialize_careers(careers: List[CareerInfo]) -> List[CareerInfoModel]:
    return [
        CareerInfoModel(
            company_name=career.company_name,
            position=career.position,
            employment_period_start=career.employment_period_start,
            employment_period_end=career.employment_period_end,
        )
        for career in careers
    ]


def serialize_certifications(
    certifications: List[Certification],
) -> List[CertificationInfoModel]:
    return [
        CertificationInfoModel(
            certification_name=certification.certification_name,
            issuing_organization=certification.issuing_organization,
            date_acquired=certification.date_acquired,
        )
        for certification in certifications
    ]


def serialize_submissions(
    submissions: list[Submission],
) -> list[SubmissionModel]:
    result = []
    for submission in submissions:
        job_posting = JobpostingListOutputModel.model_validate(
            submission.job_posting
        )
        result.append(
            SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting,
                snapshot_resume=submission.snapshot_resume,
                memo=submission.memo or "",
                is_read=submission.is_read,
                created_at=submission.created_at,
            )
        )
    return result
