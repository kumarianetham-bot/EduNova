from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    lecturer = "lecturer"
    student = "student"

class CourseStatus(str, enum.Enum):
    live = "live"
    scheduled = "scheduled"
    draft = "draft"

class AnnouncementTarget(str, enum.Enum):
    everyone = "everyone"
    students = "students"
    lecturers = "lecturers"

class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    graded = "graded"

# ─────────────────────────────────────────────
# User
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(300), nullable=False)
    role = Column(String(20), default="student")
    phone = Column(String(30), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student_profile = relationship("Student", back_populates="user", uselist=False)
    lecturer_profile = relationship("Lecturer", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")

# ─────────────────────────────────────────────
# Student
# ─────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    student_id = Column(String(50), unique=True, index=True)
    department = Column(String(100), nullable=True)
    level = Column(String(20), nullable=True)
    gpa = Column(Float, default=0.0)
    is_at_risk = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student")
    submissions = relationship("AssignmentSubmission", back_populates="student")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")

# ─────────────────────────────────────────────
# Lecturer
# ─────────────────────────────────────────────
class Lecturer(Base):
    __tablename__ = "lecturers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    lecturer_id = Column(String(50), unique=True, index=True)
    department = Column(String(100), nullable=True)
    specialization = Column(String(200), nullable=True)
    rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="lecturer_profile")
    courses = relationship("Course", back_populates="lecturer")

# ─────────────────────────────────────────────
# Course
# ─────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    course_code = Column(String(30), unique=True, index=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=True)
    status = Column(String(20), default="draft")
    cover_image_url = Column(String(500), nullable=True)
    total_weeks = Column(Integer, default=12)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lecturer = relationship("Lecturer", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")
    schedules = relationship("Schedule", back_populates="course")
    resources = relationship("Resource", back_populates="course")
    attendances = relationship("Attendance", back_populates="course")

# ─────────────────────────────────────────────
# Enrollment
# ─────────────────────────────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    completion_percentage = Column(Float, default=0.0)
    grade = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

# ─────────────────────────────────────────────
# Assignment
# ─────────────────────────────────────────────
class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    total_marks = Column(Float, default=100.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(200), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(String(20), default="submitted")

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")

# ─────────────────────────────────────────────
# Quiz
# ─────────────────────────────────────────────
class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=30)
    total_marks = Column(Float, default=100.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500))
    option_b = Column(String(500))
    option_c = Column(String(500))
    option_d = Column(String(500))
    correct_option = Column(String(1))
    marks = Column(Float, default=1.0)

    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    score = Column(Float, nullable=True)
    answers = Column(Text, nullable=True)  # JSON string
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")

# ─────────────────────────────────────────────
# Schedule
# ─────────────────────────────────────────────
class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(200), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="schedules")

# ─────────────────────────────────────────────
# Attendance
# ─────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    is_present = Column(Boolean, default=False)
    date = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")

# ─────────────────────────────────────────────
# Announcement
# ─────────────────────────────────────────────
class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    target = Column(String(20), default="everyone")  # everyone | students | lecturers
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User", foreign_keys=[admin_id])

# ─────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")

# ─────────────────────────────────────────────
# Message
# ─────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    file_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])

# ─────────────────────────────────────────────
# Resource
# ─────────────────────────────────────────────
class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    title = Column(String(300), nullable=False)
    resource_type = Column(String(30), default="file")  # file | link | folder
    file_url = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)
    file_size = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="resources")
    uploader = relationship("User", foreign_keys=[uploaded_by])

# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    submitted_by = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    lecturer_rating = Column(Float, nullable=True)
    status = Column(String(30), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reporter = relationship("User", foreign_keys=[submitted_by])
