from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-sceneid",
    version="0.1.1",
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    test_suite="tests",
    url="https://github.com/demozoo/django-sceneid/",

    author="Matt Westcott",
    author_email="matt@west.co.tt",
    description="SceneID authentication for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        'Django>=3.0,<5',
        'requests>=2,<3',
    ],
    extras_require={
        "testing": [
            'responses>=0.14,<0.21',
        ]
    },
    license="BSD",
)
