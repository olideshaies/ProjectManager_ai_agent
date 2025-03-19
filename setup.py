from setuptools import setup, find_packages

setup(
    name="project_manager",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
        "fastapi",
        "uvicorn",
        "python-dotenv",
        # ... other dependencies
    ],
)
