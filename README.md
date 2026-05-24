# EduNova API

A full-featured Learning Management System (LMS) REST API built with **FastAPI** and **SQLAlchemy**.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 3. Seed the Database
```bash
python seed.py
```

### 4. Run the Server
```bash
uvicorn main:app --reload
```

### 5. Open API Docs
Visit: **http://localhost:8000/docs**

---

## 🔐 Environment Variables

Create a `.env` file in the root folder with the following:

```dotenv
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Security
SECRET_KEY=your-long-random-secret-key

# Cloudinary File Storage
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Seed Credentials (used by seed.py only)
ADMIN_EMAIL=your_admin_email
ADMIN_PASSWORD=your_admin_password
LECTURER_EMAIL=your_lecturer_email
LECTURER_PASSWORD=your_lecturer_password
STUDENT_EMAIL=your_student_email
STUDENT_PASSWORD=your_student_password
```

> ⚠️ **Never share your `.env` file or push it to GitHub**

---

## 📁 Project Structure
edunova/
├── main.py                    # App entry point
├── seed.py                    # Database seeder
├── Procfile                   # Deployment config
├── requirements.txt
├── .env                       # Your credentials (never push)
├── .env.example               # Template for .env
├── .gitignore
├── database/
│   └── db.py                  # SQLAlchemy engine + session
├── models/
│   └── models.py              # All ORM models
├── utils/
│   ├── auth.py                # JWT auth helpers
│   └── cloudinary_upload.py   # File upload handler
└── routers/
├── auth.py                # Login / Register / Me
├── admin.py               # Admin dashboard
├── courses.py             # Course CRUD + enrollment
├── students.py            # Student management
├── lecturers.py           # Lecturer management
├── reports.py             # Reports + admin feedback
├── announcements.py       # Targeted announcements
├── notifications.py       # User notifications
├── lecturer_dashboard.py  # Lecturer dashboard
├── assignments.py         # Assignments + grading
├── quizzes.py             # Quizzes + auto-grading
├── messages.py            # Direct messaging
├── schedule.py            # Class scheduling
├── resources.py           # Files/links sharing
├── uploads.py             # Cloudinary file uploads
└── student_dashboard.py   # Student dashboard

---

## 🛣️ Key Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a user |
| POST | `/api/auth/login` | Login (returns JWT) |
| GET | `/api/auth/me` | Current user info |

### Admin Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Full dashboard stats |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/courses/` | Create course (Admin) |
| GET | `/api/courses/` | List all courses |
| GET | `/api/courses/{id}` | Course details |
| PUT | `/api/courses/{id}` | Update course (Admin) |
| POST | `/api/courses/{id}/enroll/{student_id}` | Enroll student |

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/students/` | Add student (Admin) |
| GET | `/api/students/` | All students |
| GET | `/api/students/stats` | Student stats |
| GET | `/api/students/{id}` | Student details |

### Lecturers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lecturers/` | Add lecturer (Admin) |
| GET | `/api/lecturers/` | All lecturers |
| GET | `/api/lecturers/stats` | Lecturer stats |
| GET | `/api/lecturers/{id}` | Lecturer details |

### File Uploads
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/uploads/avatar` | Upload profile photo |
| POST | `/api/uploads/assignment` | Upload assignment file |
| POST | `/api/uploads/submission` | Upload student submission |
| POST | `/api/uploads/resource` | Upload course resource |
| POST | `/api/uploads/course-thumbnail` | Upload course thumbnail |
| POST | `/api/uploads/message-file` | Upload message attachment |

### Lecturer Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/lecturer/dashboard` | Full lecturer dashboard |
| GET | `/api/lecturer/my-classes` | Courses overview |
| GET | `/api/lecturer/my-classes/{id}/students` | Students in course |

### Assignments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/assignments/` | Create assignment |
| GET | `/api/assignments/course/{id}` | Course assignments |
| GET | `/api/assignments/{id}/submissions` | All submissions |
| POST | `/api/assignments/submit` | Submit (Student) |
| PUT | `/api/assignments/submissions/{id}/grade` | Grade + feedback |

### Quizzes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/quizzes/` | Create quiz |
| GET | `/api/quizzes/course/{id}` | Course quizzes |
| POST | `/api/quizzes/attempt` | Attempt quiz (Student) |
| GET | `/api/quizzes/{id}/attempts` | All attempts |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/messages/` | Send message |
| GET | `/api/messages/inbox` | Inbox |
| GET | `/api/messages/sent` | Sent messages |
| GET | `/api/messages/conversation/{user_id}` | Full conversation |

### Schedule
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/schedule/` | Schedule a class |
| GET | `/api/schedule/upcoming` | Upcoming classes |
| GET | `/api/schedule/course/{id}` | Course schedules |

### Resources
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resources/` | Upload resource |
| GET | `/api/resources/course/{id}` | Course resources |
| DELETE | `/api/resources/{id}` | Delete resource |

### Student Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/student/dashboard` | Student dashboard |
| GET | `/api/student/my-grades` | All grades |
| GET | `/api/student/my-assignments` | Assignments + statuses |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | All notifications |
| GET | `/api/notifications/unread-count` | Unread count |
| PUT | `/api/notifications/{id}/read` | Mark as read |
| PUT | `/api/notifications/read-all` | Mark all read |

---

## 🗄️ Database

Supports **PostgreSQL** (recommended for production) and **SQLite** (for local dev).

```dotenv
# PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/dbname

# SQLite (local only)
DATABASE_URL=sqlite:///./edunova.db
```

---

## 📤 File Uploads

All file uploads are handled via **Cloudinary**. The frontend sends files directly to your API — no Cloudinary integration needed on the frontend side.

- Max file size: **10MB**
- Supported: PDF, Word, Excel, PowerPoint, images,zip
- Avatars auto-resized to **400x400**

---

## 🔑 Authentication

All protected endpoints require a Bearer token:
Get token via `POST /api/auth/login` with email and password.

---

## 🚀 Deployment

This API is configured for deployment on **Render.com** or any platform supporting Python.

The `Procfile` contains:web: uvicorn main:app --host 0.0.0.0 --port $PORT

Set all environment variables in your platform's dashboard — never in code.
