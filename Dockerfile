FROM python:3.13-slim
RUN pip install --no-cache-dir uv

# Install Node.js for MCP server
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install
COPY  pyproject.toml uv.lock ./
RUN uv sync --system --frozen

# Install MCP servers
RUN npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-memory @modelcontextprotocol/server-sequential-thinking

# Copy application code
COPY . .

# Create startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]