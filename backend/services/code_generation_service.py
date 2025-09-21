# services/code_generation_service.py - Code Generation Service
import pandas as pd
import logging
from typing import Dict, Any
from datetime import datetime
from services.data_analysis_service import DataAnalysisService

logger = logging.getLogger(__name__)

class CodeGenerationService:
    """Service for generating code artifacts like SQL, APIs, etc."""
    
    def __init__(self):
        self.data_service = DataAnalysisService()
    
    def generate_sql_schema(self, table_name: str, df: pd.DataFrame, target_db: str = "postgres") -> str:
        """Generate enhanced SQL schema with constraints."""
        if df.empty:
            return f"-- No data available for table {table_name}"
        
        # Database-specific type mappings
        type_mappings = {
            "postgres": {
                "integer": "BIGINT",
                "float": "NUMERIC(12,2)",
                "string_short": "VARCHAR(255)",
                "string_long": "TEXT",
                "date": "DATE",
                "datetime": "TIMESTAMP",
                "boolean": "BOOLEAN"
            },
            "mysql": {
                "integer": "INT",
                "float": "DECIMAL(12,2)",
                "string_short": "VARCHAR(255)",
                "string_long": "TEXT",
                "date": "DATE",
                "datetime": "DATETIME",
                "boolean": "BOOLEAN"
            },
            "sqlite": {
                "integer": "INTEGER",
                "float": "REAL",
                "string_short": "TEXT",
                "string_long": "TEXT",
                "date": "DATE",
                "datetime": "DATETIME",
                "boolean": "INTEGER"
            }
        }
        
        mapper = type_mappings.get(target_db, type_mappings["postgres"])
        
        columns = []
        constraints = []
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            null_percentage = df[col].isnull().sum() / len(df) if len(df) > 0 else 0
            
            # Determine SQL type
            if "int" in dtype:
                sql_type = mapper["integer"]
            elif "float" in dtype:
                sql_type = mapper["float"]
            else:
                max_length = df[col].astype(str).str.len().max() if not df[col].isna().all() else 0
                sql_type = mapper["string_short"] if max_length <= 255 else mapper["string_long"]
            
            # Add NOT NULL constraint if low null percentage
            not_null = " NOT NULL" if null_percentage < 0.1 else ""
            
            columns.append(f"    {col} {sql_type}{not_null}")
            
            # Add unique constraint for potential ID columns
            if "id" in col.lower() or "number" in col.lower():
                unique_vals = df[col].nunique()
                total_vals = len(df.dropna(subset=[col]))
                if unique_vals == total_vals and total_vals > 0:  # All values are unique
                    constraints.append(f"    UNIQUE ({col})")
        
        # Build CREATE TABLE statement
        sql = f"-- Generated schema for {table_name}\n"
        sql += f"-- Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        sql += f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(columns)
        
        if constraints:
            sql += ",\n" + ",\n".join(constraints)
        
        sql += "\n);\n\n"
        
        # Add indexes for common lookup columns
        index_candidates = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['id', 'number', 'code', 'date', 'name'])]
        
        sql += "-- Recommended indexes\n"
        for col in index_candidates[:5]:  # Limit to 5 indexes
            sql += f"CREATE INDEX idx_{table_name}_{col.lower()} ON {table_name}({col});\n"
        
        return sql
    
    def generate_json_schema(self, df: pd.DataFrame) -> Dict:
        """Generate enhanced JSON schema with validation rules."""
        if df.empty:
            return {}
        
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            col_schema = {}
            
            if "int" in dtype:
                min_val = df[col].min() if not df[col].isna().all() else 0
                max_val = df[col].max() if not df[col].isna().all() else 0
                col_schema = {
                    "type": "integer",
                    "minimum": int(min_val) if pd.notna(min_val) else 0,
                    "maximum": int(max_val) if pd.notna(max_val) else 0
                }
            elif "float" in dtype:
                min_val = df[col].min() if not df[col].isna().all() else 0.0
                max_val = df[col].max() if not df[col].isna().all() else 0.0
                col_schema = {
                    "type": "number",
                    "minimum": float(min_val) if pd.notna(min_val) else 0.0,
                    "maximum": float(max_val) if pd.notna(max_val) else 0.0
                }
            else:
                max_length = df[col].astype(str).str.len().max() if not df[col].isna().all() else 255
                col_schema = {
                    "type": "string",
                    "maxLength": int(max_length) if pd.notna(max_length) else 255
                }
                
                # Add enum for columns with few unique values
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 10 and len(unique_vals) > 0:
                    col_schema["enum"] = [self.data_service.convert_numpy_types(val) for val in unique_vals.tolist()]
            
            schema["properties"][col] = col_schema
            
            # Add to required if less than 10% null values
            null_percentage = df[col].isnull().sum() / len(df)
            if null_percentage < 0.1:
                schema["required"].append(col)
        
        return self.data_service.convert_numpy_types(schema)
    
    def generate_rest_api_code(self, table_name: str, df: pd.DataFrame) -> str:
        """Generate comprehensive REST API code."""
        if df.empty:
            columns_str = "# No columns available"
            pydantic_fields = "    pass"
        else:
            # Generate Pydantic model fields
            pydantic_fields = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                if "int" in dtype:
                    pydantic_fields.append(f"    {col}: Optional[int] = None")
                elif "float" in dtype:
                    pydantic_fields.append(f"    {col}: Optional[float] = None")
                else:
                    pydantic_fields.append(f"    {col}: Optional[str] = None")
            
            pydantic_fields = "\n".join(pydantic_fields)
            columns_str = f"# Columns: {', '.join(df.columns)}"

        api_code = f'''"""
Enhanced REST API for Modernized AS/400 Data
{columns_str}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/modernized_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI App
app = FastAPI(
    title="Modernized AS/400 API",
    description="RESTful API for legacy AS/400 data modernization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class {table_name.title().replace('_', '')}Base(BaseModel):
{pydantic_fields}

class {table_name.title().replace('_', '')}Create({table_name.title().replace('_', '')}Base):
    pass

class {table_name.title().replace('_', '')}Update({table_name.title().replace('_', '')}Base):
    pass

class {table_name.title().replace('_', '')}Response({table_name.title().replace('_', '')}Base):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    items: List[{table_name.title().replace('_', '')}Response]
    total: int
    page: int
    size: int
    pages: int

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "AS/400 Modernized API"
    }}

@app.get("/{table_name}", response_model=PaginatedResponse)
async def get_{table_name}(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db)
):
    """Get paginated list of {table_name} records"""
    # Implementation would query your database
    # This is a template - replace with actual database queries
    total = 0  # Get total count from database
    items = []  # Get items from database
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@app.post("/{table_name}", response_model={table_name.title().replace('_', '')}Response, status_code=status.HTTP_201_CREATED)
async def create_{table_name}(
    item: {table_name.title().replace('_', '')}Create,
    db: Session = Depends(get_db)
):
    """Create a new {table_name} record"""
    # Implementation would create record in database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Create operation not implemented yet"
    )

@app.get("/{table_name}/{{item_id}}", response_model={table_name.title().replace('_', '')}Response)
async def get_{table_name}_by_id(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific {table_name} record by ID"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{table_name.title()} not found"
    )

@app.put("/{table_name}/{{item_id}}", response_model={table_name.title().replace('_', '')}Response)
async def update_{table_name}(
    item_id: int,
    item: {table_name.title().replace('_', '')}Update,
    db: Session = Depends(get_db)
):
    """Update a {table_name} record"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update operation not implemented yet"
    )

@app.delete("/{table_name}/{{item_id}}")
async def delete_{table_name}(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete a {table_name} record"""
    return {{"message": f"{table_name.title()} deleted successfully"}}

@app.get("/{table_name}/stats")
async def get_{table_name}_stats(db: Session = Depends(get_db)):
    """Get statistics for {table_name} data"""
    return {{
        "total_records": 0,
        "last_updated": datetime.utcnow(),
        "data_quality_score": 95.0
    }}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
'''
        
        return api_code

    def generate_docker_config(self, table_name: str, target_db: str = "postgres") -> Dict[str, str]:
        """Generate Docker configuration files"""
        
        dockerfile = f'''# Dockerfile for {table_name} API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

        docker_compose = f'''version: '3.8'

services:
  # Main API Service
  {table_name}-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL={target_db}://user:password@db:5432/{table_name}_db
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Database Service
  db:
    image: {f"postgres:15" if target_db == "postgres" else f"{target_db}:latest"}
    environment:
      - POSTGRES_DB={table_name}_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d {table_name}_db"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # API Gateway (Nginx)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - {table_name}-api
    restart: unless-stopped

volumes:
  db_data:
  redis_data:
'''

        return {
            "dockerfile": dockerfile,
            "docker_compose": docker_compose
        }

# Global code generation service instance
code_service = CodeGenerationService()