import logging
from celery import shared_task
from .models import Resume, JobDescription
from matcher.models import SimilarityScore
from matcher.utils import calculate_similarity, get_match_category
from .utils import extract_text_from_file

logger = logging.getLogger(__name__)

@shared_task
def process_resume_async(resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        
        # Extract text from resume file
        if resume.file and not resume.extracted_text:
            resume.extracted_text = extract_text_from_file(resume.file)
            resume.save()
        
        # Calculate similarity scores with all active job descriptions
        active_jobs = JobDescription.objects.filter(is_active=True)
        
        for job in active_jobs:
            try:
                # Calculate similarity score
                score = calculate_similarity(resume.extracted_text, job.extracted_text)
                
                # Create or update similarity score
                SimilarityScore.objects.update_or_create(
                    resume=resume,
                    job_description=job,
                    defaults={'score': score}
                )
                
            except Exception as e:
                logger.error(f"Error calculating similarity for job {job.id}: {str(e)}")
                continue
                
    except Resume.DoesNotExist:
        logger.error(f"Resume {resume_id} not found")
    except Exception as e:
        logger.error(f"Error processing resume {resume_id}: {str(e)}")

@shared_task
def process_job_description_async(job_id):
    try:
        job = JobDescription.objects.get(id=job_id)
        
        # Extract text from job description file
        if job.file and not job.extracted_text:
            job.extracted_text = extract_text_from_file(job.file)
            job.save()
        
        # Calculate similarity scores with all resumes
        resumes = Resume.objects.all()
        
        for resume in resumes:
            try:
                # Calculate similarity score
                score = calculate_similarity(resume.extracted_text, job.extracted_text)
                
                # Create or update similarity score
                SimilarityScore.objects.update_or_create(
                    resume=resume,
                    job_description=job,
                    defaults={'score': score}
                )
                
            except Exception as e:
                logger.error(f"Error calculating similarity for resume {resume.id}: {str(e)}")
                continue
                
    except JobDescription.DoesNotExist:
        logger.error(f"Job description {job_id} not found")
    except Exception as e:
        logger.error(f"Error processing job description {job_id}: {str(e)}") 