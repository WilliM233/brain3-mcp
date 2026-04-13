FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY mcp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user (matches brain3 security pattern)
RUN addgroup --system brain3 && adduser --system --ingroup brain3 brain3

# Copy application code
COPY mcp/ ./mcp/

# Switch to non-root user
USER brain3

ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8001
ENV BRAIN3_API_URL=http://api:8000

EXPOSE 8001

CMD ["python", "mcp/server.py"]
