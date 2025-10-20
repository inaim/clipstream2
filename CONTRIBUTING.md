# Contributing to ClipStream

First off, thank you for considering contributing to ClipStream! It's people like you that make ClipStream such a great platform.

## 🌟 Ways to Contribute

- **Bug Reports**: Report bugs through GitHub Issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests for bug fixes or new features
- **Documentation**: Improve or translate documentation
- **Testing**: Help test new features and report issues
- **Design**: Contribute UI/UX improvements
- **Translations**: Add or improve language translations

---

## 🚀 Getting Started

### 1. Fork the Repository

Click the "Fork" button at the top right of the repository page.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/clipstream.git
cd clipstream
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/clipstream.git
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## 💻 Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Git

### Setup Steps

```bash
# 1. Start infrastructure services
docker-compose up -d

# 2. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration

# 3. Setup frontend
cd ../frontend
npm install
cp .env.example .env
# Edit .env with your configuration

# 4. Start development servers
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Celery Worker
cd backend
celery -A workers.video_worker worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
```

---

## 📝 Code Style Guidelines

### Frontend (TypeScript/React)

- Use **TypeScript** for all new code
- Follow **React Hooks** best practices
- Use **functional components** over class components
- Follow **Airbnb React Style Guide**
- Use **Tailwind CSS** for styling
- Keep components **small and focused**

```typescript
// Good ✅
export function VideoCard({ video }: VideoCardProps) {
  const { t } = useLanguage();
  
  return (
    <div className="rounded-lg shadow-md">
      <h3>{t('video.title')}</h3>
    </div>
  );
}

// Bad ❌
export function VideoCard(props: any) {
  return <div style={{ borderRadius: '8px' }}>
    <h3>Video Title</h3>
  </div>;
}
```

### Backend (Python/FastAPI)

- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Write **docstrings** for all public functions
- Use **async/await** for I/O operations
- Keep functions **small and focused**

```python
# Good ✅
async def get_video_by_id(video_id: str) -> Optional[Video]:
    """
    Retrieve a video by its ID.
    
    Args:
        video_id: The unique identifier of the video
        
    Returns:
        Video object if found, None otherwise
    """
    return await db.query("SELECT * FROM videos WHERE id = $id", {"id": video_id})

# Bad ❌
def get_video(id):
    return db.query("SELECT * FROM videos WHERE id = " + id)
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or tooling changes
- `perf`: Performance improvements

**Examples:**

```bash
feat(upload): add resumable upload support

Implemented tus.io protocol for resumable uploads.
Users can now pause and resume uploads even after
browser closure or network interruption.

Closes #123
```

```bash
fix(feed): resolve infinite scroll pagination bug

Fixed issue where feed would load duplicate videos
when scrolling quickly.

Fixes #456
```

---

## 🧪 Testing

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_videos.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

**Frontend:**
```typescript
import { render, screen } from '@testing-library/react';
import { VideoCard } from './VideoCard';

describe('VideoCard', () => {
  it('renders video title', () => {
    const video = { id: '1', title: 'Test Video' };
    render(<VideoCard video={video} />);
    expect(screen.getByText('Test Video')).toBeInTheDocument();
  });
});
```

**Backend:**
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_video():
    response = client.get("/api/v1/video/123")
    assert response.status_code == 200
    assert response.json()["id"] == "123"
```

---

## 🌍 Adding Translations

We support 8 languages. To add or update translations:

1. Edit `frontend/src/lib/i18n.ts`
2. Add your translation keys to all language objects
3. Use the translation in components: `{t('your.key')}`

```typescript
// i18n.ts
export const translations = {
  en: {
    'video.upload': 'Upload Video',
    'video.processing': 'Processing...',
  },
  es: {
    'video.upload': 'Subir Video',
    'video.processing': 'Procesando...',
  },
  // ... other languages
};

// Component usage
const { t } = useLanguage();
<button>{t('video.upload')}</button>
```

---

## 🐛 Reporting Bugs

### Before Submitting

1. **Check existing issues** to avoid duplicates
2. **Update to latest version** and see if the bug persists
3. **Collect information**:
   - OS and version
   - Browser and version
   - Node.js and Python versions
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots/videos if applicable

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. macOS 13.0]
 - Browser: [e.g. Chrome 120]
 - Node.js: [e.g. 18.17.0]
 - Python: [e.g. 3.11.5]

**Additional context**
Any other context about the problem.
```

---

## 💡 Feature Requests

### Before Submitting

1. **Check existing feature requests**
2. **Ensure it aligns with project goals**
3. **Consider if it benefits most users**

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Mockups, examples, or other context.
```

---

## 🔄 Pull Request Process

### 1. Ensure Your Code Meets Standards

```bash
# Frontend
npm run lint
npm run typecheck
npm run test

# Backend
black backend/
flake8 backend/
mypy backend/
pytest
```

### 2. Update Documentation

- Update README.md if needed
- Add/update code comments
- Update API documentation
- Add/update tests

### 3. Create Pull Request

- Use a clear, descriptive title
- Reference related issues
- Describe your changes in detail
- Include screenshots for UI changes
- Ensure all CI checks pass

### Pull Request Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## How Has This Been Tested?
Describe the tests you ran.

## Screenshots (if applicable)
Add screenshots here.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

---

## 📋 Code Review Process

1. **Automated Checks**: CI/CD runs linting, tests, and builds
2. **Peer Review**: At least one maintainer reviews the code
3. **Feedback**: Address any requested changes
4. **Approval**: Maintainer approves the PR
5. **Merge**: PR is merged into main branch

---

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Eligible for contributor badges
- Invited to contributor Discord channel

---

## 📞 Getting Help

- **Discord**: [Join our community](https://discord.gg/clipstream)
- **GitHub Discussions**: Ask questions and share ideas
- **Email**: dev@clipstream.io

---

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Violations may be reported to dev@clipstream.io. All complaints will be reviewed and investigated promptly and fairly.

---

Thank you for contributing to ClipStream! 🎉

