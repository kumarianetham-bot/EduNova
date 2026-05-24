from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import engine, Base
from routers import (
    uploads,
    admin, courses, students, lecturers,
    reports, announcements, notifications,
    assignments, quizzes, messages, schedule,
    resources, auth, lecturer_dashboard, student_dashboard
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduNova API",
    description="EduNova Learning Management System API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Dashboard"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(lecturers.router, prefix="/api/lecturers", tags=["Lecturers"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["Announcements"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(lecturer_dashboard.router, prefix="/api/lecturer", tags=["Lecturer Dashboard"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["File Uploads"])
app.include_router(student_dashboard.router, prefix="/api/student", tags=["Student Dashboard"])

@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to EduNova API", "version": "1.0.0", "docs": "/docs"}

