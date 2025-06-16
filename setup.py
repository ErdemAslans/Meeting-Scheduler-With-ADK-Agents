from setuptools import setup, find_packages

setup(
    name="meeting-scheduler",
    version="1.0.0",
    description="Profesyonel toplantı planlama sistemi",
    author="Meeting Scheduler Team",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client==2.110.0",
        "google-auth-httplib2==0.2.0", 
        "google-auth-oauthlib==1.2.0",
        "google-auth==2.25.2",
        "msal==1.25.0",
        "requests==2.31.0",
        "icalendar==5.0.11"
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'meeting-scheduler=main:main',
        ],
    },
)