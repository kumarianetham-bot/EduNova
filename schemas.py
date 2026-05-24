from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime

# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    full_name: str

# ─────────────────────────────────────────────
# User
# ─────────────────────────────────────────────
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Student
# ─────────────────────────────────────────────
class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None

class StudentOut(BaseModel):
    id: int
    student_id: str
    department: Optional[str]
    level: Optional[str]
    gpa: float
    is_at_risk: bool
    user: UserOut
    class Config:
        from_attributes = True

class StudentDetail(StudentOut):
    enrollments: List[Any] = []
    attendances: List[Any] = []
    submissions: List[Any] = []

# ─────────────────────────────────────────────
# Lecturer
# ─────────────────────────────────────────────
class LecturerCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None

class LecturerOut(BaseModel):
    id: int
    lecturer_id: str
    department: Optional[str]
    specialization: Optional[str]
    rating: float
    is_active: bool
    user: UserOut
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Course
# ─────────────────────────────────────────────
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course_code: str
    lecturer_id: Optional[int] = None
    status: Optional[str] = "draft"
    total_weeks: Optional[int] = 12

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    lecturer_id: Optional[int] = None
    status: Optional[str] = None
    total_weeks: Optional[int] = None

class CourseOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    course_code: str
    status: str
    total_weeks: int
    created_at: datetime
    total_enrolled: Optional[int] = 0
    completion_rate: Optional[float] = 0.0
    class Config:
        from_attributes = True

class CourseDetail(CourseOut):
    lecturer: Optional[LecturerOut] = None

# ─────────────────────────────────────────────
# Enrollment
# ─────────────────────────────────────────────
class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int

class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime
    completion_percentage: float
    grade: Optional[float]
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Assignment
# ─────────────────────────────────────────────
class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    total_marks: Optional[float] = 100.0

class AssignmentOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    total_marks: float
    created_at: datetime
    total_submissions: Optional[int] = 0
    class Config:
        from_attributes = True

class GradeSubmissionRequest(BaseModel):
    score: float
    feedback: Optional[str] = None

class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    file_url: Optional[str]
    file_name: Optional[str]
    submitted_at: datetime
    score: Optional[float]
    feedback: Optional[str]
    status: str
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Quiz
# ─────────────────────────────────────────────
class QuizQuestionCreate(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    marks: Optional[float] = 1.0

class QuizCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = 30
    total_marks: Optional[float] = 100.0
    questions: Optional[List[QuizQuestionCreate]] = []

class QuizOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    duration_minutes: int
    total_marks: float
    created_at: datetime
    total_questions: Optional[int] = 0
    class Config:
        from_attributes = True

class QuizAttemptCreate(BaseModel):
    answers: str  # JSON string: {"question_id": "A", ...}

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    score: Optional[float]
    submitted_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Schedule
# ─────────────────────────────────────────────
class ScheduleCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_link: Optional[str] = None

class ScheduleOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    meeting_link: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Announcement
# ─────────────────────────────────────────────
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    target: str = "everyone"  # everyone | students | lecturers

class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    target: str
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    notification_type: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Message
# ─────────────────────────────────────────────
class MessageCreate(BaseModel):
    receiver_id: int
    content: str
    file_url: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    file_url: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Resource
# ─────────────────────────────────────────────
class ResourceCreate(BaseModel):
    course_id: Optional[int] = None
    title: str
    resource_type: str = "file"
    file_url: Optional[str] = None
    link_url: Optional[str] = None
    file_size: Optional[str] = None

class ResourceOut(BaseModel):
    id: int
    course_id: Optional[int]
    title: str
    resource_type: str
    file_url: Optional[str]
    link_url: Optional[str]
    file_size: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────
class ReportCreate(BaseModel):
    report_type: str
    title: str
    content: str
    lecturer_rating: Optional[float] = None

class ReportOut(BaseModel):
    id: int
    report_type: str
    title: str
    content: str
    lecturer_rating: Optional[float]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# ─────────────────────────────────────────────
# Dashboard / Analytics
# ─────────────────────────────────────────────
class AdminDashboardStats(BaseModel):
    total_students: int
    total_lecturers: int
    total_courses: int
    active_classes: int
    enrollment_graph: List[dict]
    course_stats: List[dict]
    top_students: List[dict]
    recent_activities: List[dict]
    upcoming_sessions: List[dict]
    completion_rate: float

class LecturerDashboardStats(BaseModel):
    total_classes: int
    total_assignments: int
    total_quizzes: int
    class_overview_graph: List[dict]
    upcoming_classes: List[dict]
    recent_activities: List[dict]
    student_engagement: List[dict]
    announcements: List[dict]
