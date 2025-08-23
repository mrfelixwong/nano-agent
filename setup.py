from setuptools import setup, find_packages

setup(
    name="nano-agent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["typer", "requests"],
    python_requires=">=3.7",
    author="Felix",
    description="Learn AI agents from scratch. 296 lines. No frameworks.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nano-agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)