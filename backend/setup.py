from setuptools import setup, find_packages

setup(
    name="tippspiel",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.11.1",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "email-validator>=2.0.0",
        "fastf1>=3.0.0",
        "pandas>=2.0.0",
        "aiosqlite>=0.19.0",
        "httpx>=0.24.0",
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "google-cloud-storage>=2.10.0",
        "python-dotenv>=1.0.0",
        "fastapi-utils>=0.2.1",
    ],
    extras_require={
        "dev": [
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ]
    },
    python_requires=">=3.9",
) 