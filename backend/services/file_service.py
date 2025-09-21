# services/file_service.py - Enhanced File Processing Service
import pandas as pd
import io
import csv
import chardet
import logging
import re
import json
from typing import Optional, Tuple, List, Any, Dict
from fastapi import HTTPException, UploadFile

# Import the AI service
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

class FileProcessingService:
    """Enhanced service for processing uploaded files with better AS/400 support"""

    @staticmethod
    def safe_decode(raw_bytes: bytes) -> str:
        """Detect encoding and decode bytes to string."""
        try:
            detect = chardet.detect(raw_bytes)
            enc = detect.get("encoding") or "utf-8"
            return raw_bytes.decode(enc, errors="ignore")
        except Exception:
            return raw_bytes.decode("utf-8", errors="ignore")

    @staticmethod
    def detect_fixed_width_structure(lines: List[str]) -> Optional[List[tuple]]:
        """
        Detect fixed-width column structure from AS/400 reports
        Returns list of (start_pos, end_pos, column_name) tuples
        """
        if len(lines) < 3:
            return None
            
        # Look for header patterns in first few lines
        header_line = None
        data_start_line = None
        
        # Common AS/400 report patterns
        for i, line in enumerate(lines[:5]):
            # Skip empty lines and separator lines (dashes, equals)
            if not line.strip() or re.match(r'^[-=\s]+$', line.strip()):
                continue
                
            # Look for lines with mixed alphanumeric content (likely headers)
            if re.search(r'[A-Za-z]', line) and not line.strip().startswith(('Page', 'Date', 'Time')):
                if header_line is None:
                    header_line = line
                    header_line_idx = i
                else:
                    # Second non-empty line might be data start
                    data_start_line = i
                    break
        
        if not header_line:
            return None
            
        # Extract column positions based on header spacing
        columns = []
        words = []
        current_word = ""
        start_pos = 0
        
        # Parse header to find column boundaries
        for pos, char in enumerate(header_line):
            if char.isspace():
                if current_word:
                    words.append((start_pos, pos, current_word.strip()))
                    current_word = ""
                    start_pos = pos + 1
                else:
                    start_pos = pos + 1
            else:
                current_word += char
        
        # Add the last word
        if current_word:
            words.append((start_pos, len(header_line), current_word.strip()))
        
        return words if len(words) > 1 else None

    @staticmethod
    def parse_fixed_width_data(content_str: str) -> pd.DataFrame:
        """
        Parse AS/400 fixed-width format data
        """
        lines = content_str.strip().split('\n')
        
        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        
        if len(lines) < 2:
            raise ValueError("Insufficient data for fixed-width parsing")
        
        # Try to detect column structure
        column_structure = FileProcessingService.detect_fixed_width_structure(lines)
        
        if column_structure:
            # Use detected structure
            columns = []
            data_rows = []
            
            # Find where actual data starts (skip headers and separators)
            data_start = 0
            for i, line in enumerate(lines):
                if re.match(r'^[-=\s]+$', line.strip()):
                    data_start = i + 1
                    break
                elif i > 0 and not re.search(r'^[A-Z][A-Z0-9\s]*$', line.strip()):
                    data_start = i
                    break
            
            # Extract column names and positions
            for start, end, name in column_structure:
                columns.append(name)
            
            # Extract data using fixed positions
            for line in lines[max(data_start, 1):]:
                if not line.strip() or re.match(r'^[-=\s]*$', line.strip()):
                    continue
                    
                row = []
                for start, end, _ in column_structure:
                    # Safely extract text within bounds
                    if start < len(line):
                        cell_value = line[start:min(end, len(line))].strip()
                        row.append(cell_value if cell_value else "")
                    else:
                        row.append("")
                
                if any(cell for cell in row):  # Skip completely empty rows
                    data_rows.append(row)
            
            if data_rows:
                df = pd.DataFrame(data_rows, columns=columns)
                logger.info(f"Fixed-width parsing successful: {df.shape}")
                return df
        
        # Fallback to pandas read_fwf
        try:
            df = pd.read_fwf(io.StringIO(content_str))
            if df.shape[1] > 1 and len(df) > 0:
                logger.info(f"Pandas fixed-width parsing: {df.shape}")
                return df
        except Exception as e:
            logger.warning(f"Pandas fixed-width parsing failed: {e}")
        
        raise ValueError("Could not parse as fixed-width format")

    @staticmethod
    def detect_delimiter_and_read_text(content_str: str) -> pd.DataFrame:
        """
        Enhanced text file parsing with strong AS/400 fixed-width support
        """
        # First, try to detect if this is a fixed-width format
        lines = [line for line in content_str.splitlines() if line.strip()]
        
        if len(lines) >= 3:
            # Check for AS/400 report characteristics
            has_uniform_width = len(set(len(line) for line in lines[:10])) <= 2
            has_header_pattern = any(
                re.search(r'^[A-Z][A-Z0-9\s]{10,}', line) 
                for line in lines[:3]
            )
            has_separator_line = any(
                re.match(r'^[-=\s]+$', line.strip()) 
                for line in lines[:5]
            )
            
            if has_uniform_width or has_header_pattern or has_separator_line:
                try:
                    return FileProcessingService.parse_fixed_width_data(content_str)
                except Exception as e:
                    logger.warning(f"Fixed-width parsing failed: {e}")
        
        # Standard CSV/delimited parsing fallback
        sample = content_str[:8192]
        delimiter = None
        
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
            logger.info(f"Detected delimiter: '{delimiter}'")
        except Exception as e:
            logger.info(f"CSV sniffer failed: {e}")
        
        # Try detected delimiter first
        if delimiter:
            try:
                df = pd.read_csv(io.StringIO(content_str), sep=delimiter, engine="python")
                if df.shape[1] > 1 and len(df) > 0:
                    logger.info(f"Successfully parsed with delimiter '{delimiter}': {df.shape}")
                    return df
            except Exception as e:
                logger.warning(f"Failed to parse with detected delimiter '{delimiter}': {e}")

        # Try common delimiters
        delimiters_to_try = [',', '\t', '|', ';', ' ']
        for delim in delimiters_to_try:
            try:
                df = pd.read_csv(io.StringIO(content_str), sep=delim, engine="python")
                if df.shape[1] > 1 and len(df) > 0:
                    logger.info(f"Successfully parsed with '{delim}': {df.shape}")
                    return df
            except Exception:
                continue

        # Manual parsing as last resort
        if not lines:
            raise ValueError("No data found in file")

        header_line = lines[0]
        data_lines = lines[1:] if len(lines) > 1 else []

        # Simple heuristic for header detection
        header_tokens = header_line.split()
        is_header = any(not token.replace('.', '').replace('-', '').isdigit() for token in header_tokens)

        if is_header and data_lines:
            headers = header_tokens
            rows = []
            for line in data_lines:
                tokens = line.split()
                while len(tokens) < len(headers):
                    tokens.append("")
                rows.append(tokens[:len(headers)])
            
            if rows:
                df = pd.DataFrame(rows, columns=headers)
                logger.info(f"Manual parsing successful: {df.shape}")
                return df

        raise ValueError("Unable to parse text file into tabular structure")

    def _modernize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Modernize column names with validation"""
        modernized_columns = []
        
        for i, col_name in enumerate(df.columns):
            original_col = str(col_name).strip()
            
            if not original_col or original_col.lower().startswith(('unnamed', 'col_', 'empty')):
                column_data = df.iloc[:, i].dropna().astype(str).tolist()
                new_name = ai_service.predict_column_name_from_data(column_data, i)
            else:
                new_name = ai_service.modernize_column_name(original_col)
            
            # Final validation
            if not new_name or len(new_name) < 2:
                new_name = f"column_{i}"
                
            modernized_columns.append(new_name)
        
        df.columns = modernized_columns
        return df

    def generate_json_export(self, df: pd.DataFrame, file_info: dict) -> Dict:
        """Generate JSON representation of the processed data"""
        try:
            # Create comprehensive JSON structure
            json_data = {
                "metadata": {
                    "filename": file_info.get("filename"),
                    "size_bytes": file_info.get("size_bytes"),
                    "detected_format": file_info.get("detected_format"),
                    "rows_processed": len(df),
                    "columns_processed": len(df.columns),
                    "processing_timestamp": pd.Timestamp.now().isoformat(),
                    "ai_processing_enabled": file_info.get("ai_processing_enabled", False)
                },
                "schema": {
                    "columns": [
                        {
                            "name": col,
                            "index": i,
                            "data_type": str(df[col].dtype),
                            "non_null_count": int(df[col].count()),
                            "null_count": int(df[col].isnull().sum()),
                            "unique_count": int(df[col].nunique())
                        }
                        for i, col in enumerate(df.columns)
                    ]
                },
                "data": df.to_dict(orient="records"),
                "statistics": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
                    "completeness_ratio": float(df.count().sum() / (len(df) * len(df.columns)))
                }
            }
            
            # Add column mapping if available
            if hasattr(file_info, 'original_columns') and hasattr(file_info, 'modernized_columns'):
                json_data["column_mapping"] = {
                    orig: modern for orig, modern in 
                    zip(file_info.get('original_columns', []), 
                        file_info.get('modernized_columns', []))
                }
            
            return json_data
            
        except Exception as e:
            logger.error(f"JSON export generation failed: {e}")
            # Return minimal JSON structure
            return {
                "metadata": {"error": str(e)},
                "data": df.head(100).to_dict(orient="records") if not df.empty else []
            }

    async def process_file(self, file: UploadFile, export_format: str = "pandas") -> Tuple[pd.DataFrame, dict]:
        """
        Process uploaded file and return DataFrame with modernized column names
        
        Args:
            file: The uploaded file
            export_format: "pandas" or "json" - format for additional export
        """
        try:
            # Read and decode file
            raw = await file.read()
            text = self.safe_decode(raw)
            logger.info(f"Processing file: {file.filename} ({len(raw)} bytes)")

            # Determine file type
            filename = (file.filename or "").lower()
            ext = filename.split(".")[-1] if "." in filename else ""

            df = None
            file_info = {
                "filename": file.filename,
                "size_bytes": len(raw),
                "detected_format": ext or "text",
                "original_columns": [],
                "modernized_columns": [],
                "export_format": export_format
            }

            # Parse based on file extension
            if ext in ("xls", "xlsx"):
                try:
                    df = pd.read_excel(io.BytesIO(raw), engine='openpyxl')
                    logger.info(f"Excel file parsed: {df.shape}")
                except Exception as e:
                    logger.error(f"Excel parsing failed: {e}")
                    raise HTTPException(status_code=400, detail=f"Could not read Excel file: {e}")

            elif ext == "csv":
                try:
                    df = pd.read_csv(io.StringIO(text), engine="python")
                    logger.info(f"CSV parsed with pandas: {df.shape}")
                except Exception:
                    logger.info("Pandas CSV parsing failed, trying enhanced detection")
                    df = self.detect_delimiter_and_read_text(text)

            else:  # TXT or unknown - Enhanced for AS/400 fixed-width
                try:
                    df = self.detect_delimiter_and_read_text(text)
                    logger.info(f"Text file parsed: {df.shape}")
                except Exception as e:
                    logger.error(f"Text parsing failed: {e}")
                    raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

            # Data validation and cleanup
            if df is None or df.empty:
                raise HTTPException(status_code=400, detail="No data found in file")

            # Store original column names
            original_columns = [str(col) for col in df.columns]
            file_info["original_columns"] = original_columns

            # Clean column names temporarily
            df.columns = [
                str(c) if str(c).strip() != "" else f"col_{i}"
                for i, c in enumerate(df.columns)
            ]

            # Remove completely empty rows
            original_row_count = len(df)
            df = df.dropna(how='all')
            
            if df.empty:
                raise HTTPException(status_code=400, detail="No valid data rows found")

            logger.info(f"Removed {original_row_count - len(df)} empty rows")

            # Modernize column names
            df = self._modernize_column_names(df)
            
            # Store modernized column names
            file_info["modernized_columns"] = list(df.columns)

            # Update file info
            file_info.update({
                "rows_processed": len(df),
                "columns_processed": len(df.columns),
                "ai_processing_enabled": ai_service.has_transformers
            })

            # Generate JSON export if requested
            if export_format == "json":
                file_info["json_export"] = self.generate_json_export(df, file_info)

            return df, file_info

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file processing: {e}")
            raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")


# Global file processing service instance
file_service = FileProcessingService()