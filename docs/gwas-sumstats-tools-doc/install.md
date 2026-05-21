# Step-by-Step Setup Guide
----
## Requirements for Installing Packages
### Verify Python Version
Before proceeding, ensure that you have Python version 3.9 to 3.11 installed on your computer. You can verify your Python version by opening a terminal or command prompt and executing either of the following commands:
```bash
$ python --version
# or 
$ python3 --version
```
### Check PIP Availability
Additionally, ensure that you have PIP available. You can verify this by running:
```bash
$ pip --version
```

## Install GWAS-Sumstat-Tools
### Installing via PIP

```bash
$ pip install gwas-sumstats-tools
```
This command installs the latest version of GWAS-Sumstat-Tools, which is recommended for users. If you prefer to install a specific previous version, you can specify the version number during installation using:

```bash
$ pip install "gwas-sumstats-tools==1.0.6"
```
To confirm successful installation of GWAS-Sumstat-Tools, run the command `gwas-ssf --help` in your terminal. This command will display the help message for the tool, confirming its installation and accessibility.

![gwas-ssf](/img/gwas-demo.gif)

### Optional Installation and Execution Methods for GWAS-Sumstat-Tools 
If the Python version displayed is not within the range of Python 3.9 to Python 3.11, you may encounter compatibility issues with the package. In such cases, you have two options:

#### Option 1: Install Python 3.9 locally
1. Download and install Python 3.9 from the [official Python website](https://www.python.org/downloads/).
2. Determine the installation location of Python 3.9 by running:
```bash
$ where python3.9
```
3. Create a virtual environment with Python 3.9 using `venv`. Navigate to your project directory (replace `<DIR>` with your actual project directory) in the terminal and run:
```bash
$ python3.9 -m venv <DIR>
```
4. Activate the virtual environment.
```bash
$ source <DIR>/bin/activate
```
5. Once the virtual environment is activated, you can install gwas-sumstats-tools using pip:
```bash
$ pip install gwas-sumstats-tools
```
6. To check if gwas-sumstats-tools was successfully installed use `gwas-ssf --help`.

7. You can now use gwas-sumstats-tools within the activated virtual environment. When you're done, you can deactivate the virtual environment by running:
```bash
$ deactivate
```
> Please refer to [installing-packages](https://packaging.python.org/en/latest/tutorials/installing-packages/) for more detail information on how to install packages 

#### Option 2: Run with docker or singularity
1. Check if the Docker **OR** Singularity is available
```bash
# docker
$ docker --version
# singularity
$ singularity --version
```
> please read how to install [Docker](https://docs.docker.com/engine/install/) or [Singularity](https://docs.sylabs.io/guides/2.6/user-guide/quick_start.html)

2. Run with docker
```bash
$ docker run -it -v $path_installed_docker ebispot/gwas-sumstats-tools:latest
```

3. **OR** Run with singularity
```bash
# pull and build the docker image to a singularity image
$ singularity build gwas-sumstats-tools.sif docker://ebispot/gwas-sumstats-tools:latest
# Run the singularity image
$ singularity shell gwas-sumstats-tools.sif
```
----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
