import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="data-splitter",
    version="0.0.2",
    author="Dawid Jurkiewicz",
    author_email="dawjur@amu.edu.pl",
    description="Hash function based data splitter.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/siulkilulki/data-splitter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={'console_scripts': ['splitter=data_splitter.splitter:main']})
