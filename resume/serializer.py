from typing import List

from job_posting.models import JobPostingBookmark
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
        is_bookmarked = (
            True
            if JobPostingBookmark.objects.filter(
                job_posting=submission.job_posting
            ).exists()
            else False
        )
        job_posting = JobpostingListOutputModel(
            job_posting_id=submission.job_posting.job_posting_id,
            job_posting_title=submission.job_posting.job_posting_title,
            city=submission.job_posting.city,
            district=submission.job_posting.district,
            company_name=submission.job_posting.company_id.company_name,
            company_address=submission.job_posting.company_id.company_address,
            summary=submission.job_posting.summary,
            deadline=submission.job_posting.deadline,
            is_bookmarked=is_bookmarked,
        )
        result.append(
            SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting,
                snapshot_resume=submission.snapshot_resume,
                memo=submission.memo or "",
                is_read=submission.is_read,
                created_at=submission.created_at.date(),
            )
        )
    return result
