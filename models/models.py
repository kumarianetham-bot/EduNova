from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Table, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base
import enum

# ─── Enums ────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    lecturer = "lecturer"
    student = "student"

class CourseStatus(str, enum.Enum):
    live = "live"
    scheduled = "scheduled"
    draft = "draft"

class AnnouncementTarget(str, enum.Enum):
    all = "all"
    lecturers = "lecturers"
    students = "students"

class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    graded = "graded"

class MessageStatus(str, enum.Enum):
    sent = "sent"
    read = "read"

class ResourceType(str, enum.Enum):
    file = "file"
    link = "link"
    folder = "folder"

# ─── Association Tables ───────────────────────────────────
course_enrollment = Table(
    "course_enrollment", Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
    Column("enrolled_at", DateTime, default=func.now()),
    Column("completion_rate", Float, default=0.0),
    Column("grade", Float, nullable=True),
    Column("attendance_rate", Float, default=0.0),
)

# ─── User ─────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# ─── Student ──────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    student_id = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    at_risk = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")
    enrollments = relationship("Course", secondary=course_enrollment, back_populates="students")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="student")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")

# ─── Lecturer ─────────────────────────────────────────────
class Lecturer(Base):
    __tablename__ = "lecturers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    lecturer_id = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")
    courses = relationship("Course", back_populates="lecturer")
    reports = relationship("Report", back_populates="lecturer")

# ─── Course ───────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String, unique=True, index=True)
    status = Column(Enum(CourseStatus), default=CourseStatus.draft)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=True)
    thumbnail_url = Column(String, nullable=True)
    duration_hours = Column(Float, default=0.0)
    total_students = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    lecturer = relationship("Lecturer", back_populates="courses")
    students = relationship("Student", secondary=course_enrollment, back_populates="enrollments")
    assignments = relationship("Assignment", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")
    schedules = relationship("ClassSchedule", back_populates="course")
    resources = relationship("Resource", back_populates="course")
    attendance_records = relationship("AttendanceRecord", back_populates="course")

# ─── Class Schedule ───────────────────────────────────────
class ClassSchedule(Base):
    __tablename__ = "class_schedules"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    meeting_link = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="schedules")
    lecturer = relationship("Lecturer")

# ─── Attendance ───────────────────────────────────────────
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    schedule_id = Column(Integer, ForeignKey("class_schedules.id"), nullable=True)
    attended = Column(Boolean, default=False)
    date = Column(DateTime, default=func.now())

    student = relationship("Student", back_populates="attendance_records")
    course = relationship("Course", back_populates="attendance_records")

# ─── Assignment ───────────────────────────────────────────
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    total_marks = Column(Float, default=100.0)
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="assignments")
    lecturer = relationship("Lecturer")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    file_url = Column(String, nullable=True)
    text_answer = Column(Text, nullable=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.submitted)
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=func.now())
    graded_at = Column(DateTime, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignment_submissions")

# ─── Quiz ─────────────────────────────────────────────────
class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30)
    total_marks = Column(Float, default=100.0)
    questions = Column(JSON, nullable=True)  # [{question, options, answer, marks}]
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="quizzes")
    lecturer = relationship("Lecturer")
    attempts = relationship("QuizAttempt", back_populates="quiz")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    answers = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=func.now())

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")

# ─── Announcement ─────────────────────────────────────────
class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    target = Column(Enum(AnnouncementTarget), default=AnnouncementTarget.all)
    created_at = Column(DateTime, default=func.now())

    admin = relationship("User")

# ─── Notification ─────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String, default="general")
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")

# ─── Message ──────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    file_url = Column(String, nullable=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.sent)
    sent_at = Column(DateTime, default=func.now())

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

# ─── Resource ─────────────────────────────────────────────
class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    uploader_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(Enum(ResourceType), default=ResourceType.file)
    url = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    is_shared_with_students = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="resources")
    uploader = relationship("User")

# ─── Report ───────────────────────────────────────────────
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"))
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    report_type = Column(String, default="progress")
    rating = Column(Float, nullable=True)
    admin_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    lecturer = relationship("Lecturer", back_populates="reports")
    admin = relationship("User")
