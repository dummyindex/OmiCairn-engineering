FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    python3 \
    python3-pip \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install R and required system libraries for R packages
RUN apt-get update && apt-get install -y \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages: CRAN packages first
RUN R -e "install.packages(c('survival', 'survminer', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'BiocManager'), repos='https://cran.rstudio.com/')"

# Install Bioconductor packages for differential expression and enrichment analysis
RUN R -e "BiocManager::install(c('DESeq2', 'edgeR', 'limma', 'clusterProfiler', 'org.Hs.eg.db', 'enrichplot', 'DOSE', 'pathview'), ask=FALSE, update=FALSE)"

# Install Node.js 20.x (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Install Python dependencies (base)
RUN pip3 install --no-cache-dir \
    boto3 \
    requests \
    Pillow \
    PyMuPDF

# Install scientific Python libraries for data analysis
# These are commonly needed by Claude Code when generating analysis scripts
RUN pip3 install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    scipy \
    scikit-learn \
    statsmodels \
    plotly \
    openpyxl \
    xlrd \
    pyarrow \
    h5py

# Install bioinformatics libraries (for genomics tasks)
RUN pip3 install --no-cache-dir \
    biopython \
    scanpy \
    anndata

# Create non-root user (required for --dangerously-skip-permissions flag)
RUN useradd -m -s /bin/bash claudeuser

# Copy application code
COPY . /app
WORKDIR /app

# Make scripts executable (including ragtool which has no extension)
RUN chmod +x /app/scripts/*.sh /app/scripts/*.py /app/scripts/ragtool

# Set up working directories for Claude Code
RUN mkdir -p /omicairn/inputs /omicairn/outputs /omicairn/workspace /omicairn/control/logs

# Copy CLAUDE.md for project-level instructions
COPY CLAUDE.md /omicairn/workspace/CLAUDE.md

# Create ragtool symbolic link (must be done as root before switching user)
RUN ln -s /app/scripts/ragtool /usr/local/bin/ragtool

# Create .claude directory structure for claudeuser (must be done as root)
RUN mkdir -p /home/claudeuser/.claude/debug /home/claudeuser/.claude/skills

# Copy skills before switching user
COPY skills /home/claudeuser/.claude/skills

# Give claudeuser ownership of working directories and .claude directory
RUN chown -R claudeuser:claudeuser /omicairn /app /home/claudeuser/.claude

# Set working directory to workspace for Claude Code
WORKDIR /omicairn/workspace

# Switch to non-root user
USER claudeuser

ENTRYPOINT ["/app/scripts/start_claude_code.sh"]
