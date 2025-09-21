# routers/modernization.py - Enhanced Modernization API Router
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime

from services.file_service import file_service
from services.ai_service import ai_service
from services.data_analysis_service import data_service
from services.code_generation_service import code_service
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/modernize")
async def modernize_file(
    file: UploadFile = File(...),
    target_db: Optional[str] = Query(default="postgres", description="Target database type"),
    table_name: Optional[str] = Query(default="modernized_table", description="Table name for generated schema"),
    export_format: Optional[str] = Query(default="pandas", description="Export format: 'pandas' or 'json'")
):
    """
    Enhanced modernization endpoint with comprehensive analysis and JSON export option.
    """
    start_time = datetime.utcnow()
    
    # Validate file size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Validate export format
    if export_format not in ["pandas", "json"]:
        raise HTTPException(
            status_code=400,
            detail="export_format must be either 'pandas' or 'json'"
        )
    
    try:
        # Process the uploaded file with export format option
        logger.info(f"Processing file: {file.filename} with export format: {export_format}")
        df, file_info = await file_service.process_file(file, export_format)
        
        # AI-powered column modernization (already handled in file_service)
        logger.info("Column modernization completed via file service")
        
        # Create column mapping for response
        original_columns = file_info.get("original_columns", [])
        modernized_columns = file_info.get("modernized_columns", [])
        
        mapping = {}
        if len(original_columns) == len(modernized_columns):
            mapping = {orig: modern for orig, modern in zip(original_columns, modernized_columns)}
        else:
            # Fallback mapping
            mapping = {f"col_{i}": col for i, col in enumerate(modernized_columns)}

        # Comprehensive analysis
        logger.info("Performing data analysis")
        
        # Convert to records (limit for performance)
        max_records = settings.MAX_RECORDS_DISPLAY
        modernized_table = df.head(max_records).fillna("").to_dict(orient="records")
        modernized_table = data_service.convert_numpy_types(modernized_table)
        
        # Generate analysis and artifacts
        data_quality = data_service.analyze_data_quality(df)
        column_stats = data_service.analyze_column_statistics(df)
        recommendations = data_service.generate_data_recommendations(df, data_quality)
        
        # Generate code artifacts
        json_schema = code_service.generate_json_schema(df)
        sql_schema = code_service.generate_sql_schema(table_name, df, target_db)
        rest_api_code = code_service.generate_rest_api_code(table_name, df)
        docker_config = code_service.generate_docker_config(table_name, target_db)
        microservices_arch = data_service.generate_microservices_architecture(df)

        # Processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Modernization completed in {processing_time:.2f} seconds")

        # Build response
        response_data = {
            "status": "success",
            "processing_time": processing_time,
            "file_info": file_info,
            "modernized_table": modernized_table,
            "mapping": mapping,
            "data_quality": data_quality,
            "column_statistics": column_stats,
            "recommendations": recommendations,
            "json_schema": json_schema,
            "sql_schema": sql_schema,
            "rest_api_code": rest_api_code,
            "docker_config": docker_config,
            "microservices_architecture": microservices_arch,
            "ai_status": ai_service.get_status()
        }
        
        # Add JSON export if requested
        if export_format == "json" and "json_export" in file_info:
            response_data["json_export"] = file_info["json_export"]
            logger.info("JSON export included in response")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during modernization: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Modernization error: {str(e)}"
        )

@router.get("/modernize/preview/{data_type}")
async def preview_modernization(data_type: str):
    """Preview how sample data would be modernized"""
    from routers.samples import get_sample_data
    
    try:
        sample = await get_sample_data(data_type)
        
        # Process sample data through modernization preview
        import pandas as pd
        import io
        
        text = sample["data"]
        df = pd.read_csv(io.StringIO(text))
        
        # Apply modernization to first few columns
        mapping = {}
        for orig in df.columns[:5]:  # Limit for preview
            new_name = ai_service.modernize_column_name(orig)
            mapping[orig] = new_name
        
        return {
            "original_columns": sample["columns"],
            "modernized_mapping": mapping,
            "preview_data": df.head(3).to_dict(orient="records"),
            "description": sample["description"]
        }
        
    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@router.get("/analyze/{data_type}")
async def analyze_sample_data(data_type: str):
    """Get detailed analysis of sample data"""
    from routers.samples import get_sample_data
    
    try:
        sample = await get_sample_data(data_type)
        
        import pandas as pd
        import io
        
        text = sample["data"]
        df = pd.read_csv(io.StringIO(text))
        
        # Perform analysis
        data_quality = data_service.analyze_data_quality(df)
        column_stats = data_service.analyze_column_statistics(df)
        recommendations = data_service.generate_data_recommendations(df, data_quality)
        microservices = data_service.generate_microservices_architecture(df)
        
        return {
            "data_type": data_type,
            "description": sample["description"],
            "data_quality": data_quality,
            "column_statistics": column_stats,
            "recommendations": recommendations,
            "microservices_architecture": microservices,
            "preview_data": df.head(5).to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@router.post("/export/json")
async def export_as_json(
    file: UploadFile = File(...),
    include_metadata: bool = Query(default=True, description="Include metadata in JSON export"),
    include_schema: bool = Query(default=True, description="Include schema information"),
    max_rows: Optional[int] = Query(default=None, description="Maximum number of rows to export")
):
    """
    Export uploaded file directly as JSON with optional metadata and schema information
    """
    try:
        # Process file for JSON export
        df, file_info = await file_service.process_file(file, export_format="json")
        
        # Limit rows if specified
        if max_rows and max_rows > 0:
            df = df.head(max_rows)
        
        # Generate JSON export
        json_export = file_service.generate_json_export(df, file_info)
        
        # Filter response based on parameters
        if not include_metadata:
            json_export.pop("metadata", None)
            json_export.pop("statistics", None)
        
        if not include_schema:
            json_export.pop("schema", None)
            json_export.pop("column_mapping", None)
        
        return JSONResponse(
            content=json_export,
            headers={
                "Content-Disposition": f"attachment; filename={file.filename}.json",
                "Content-Type": "application/json"
            }
        )
        
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        raise HTTPException(status_code=500, detail=f"JSON export error: {str(e)}")

@router.get("/formats/supported")
async def get_supported_formats():
    """Get list of supported file formats and their capabilities"""
    return {
        "supported_formats": {
            "csv": {
                "description": "Comma-separated values",
                "extensions": [".csv"],
                "parsing_methods": ["delimiter_detection", "pandas_csv"],
                "ai_modernization": True
            },
            "txt": {
                "description": "Text files including AS/400 fixed-width reports",
                "extensions": [".txt"],
                "parsing_methods": ["fixed_width_detection", "delimiter_detection", "manual_parsing"],
                "ai_modernization": True,
                "special_features": ["as400_fixed_width", "report_parsing"]
            },
            "excel": {
                "description": "Microsoft Excel files",
                "extensions": [".xlsx", ".xls"],
                "parsing_methods": ["openpyxl", "xlrd"],
                "ai_modernization": True
            }
        },
        "export_formats": {
            "pandas": "Standard DataFrame processing with modernized columns",
            "json": "Complete JSON export with metadata, schema, and data"
        },
        "ai_features": {
            "column_modernization": "Transform AS/400 column names to modern snake_case",
            "pattern_recognition": "Recognize 200+ common AS/400 naming conventions",
            "data_inference": "Predict column names from data content"
        }
    }