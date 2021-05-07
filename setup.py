from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-sceneid",
    version="0.1",
    packages=["sceneid"],
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
        "Framework :: Django :: 3",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        'requests>=2,<3',
    ],
    extras_require={
        "testing": [
        ]
    },
    license="BSD",
)
