# services/data_analysis_service.py - Data Analysis & Quality Service
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAnalysisService:
    """Service for data quality analysis and insights"""
    
    @staticmethod
    def convert_numpy_types(obj):
        """Convert NumPy types to native Python types for JSON serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: DataAnalysisService.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [DataAnalysisService.convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality metrics."""
        if df.empty:
            return {}
        
        metrics = {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "missing_values": {col: int(count) for col, count in df.isnull().sum().to_dict().items()},
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
            "unique_counts": {col: int(count) for col, count in df.nunique().to_dict().items()},
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "quality_score": float(round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2)) if len(df) > 0 else 0.0
        }
        
        return self.convert_numpy_types(metrics)
    
    def analyze_column_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get detailed statistics for each column"""
        if df.empty:
            return {}
        
        stats = {}
        
        for col in df.columns:
            col_data = df[col]
            col_stats = {
                "name": col,
                "dtype": str(col_data.dtype),
                "count": int(col_data.count()),
                "null_count": int(col_data.isnull().sum()),
                "null_percentage": float(round((col_data.isnull().sum() / len(df)) * 100, 2)),
                "unique_count": int(col_data.nunique())
            }
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(col_data):
                col_stats.update({
                    "mean": float(col_data.mean()) if not col_data.isna().all() else None,
                    "median": float(col_data.median()) if not col_data.isna().all() else None,
                    "std": float(col_data.std()) if not col_data.isna().all() else None,
                    "min": float(col_data.min()) if not col_data.isna().all() else None,
                    "max": float(col_data.max()) if not col_data.isna().all() else None,
                    "q25": float(col_data.quantile(0.25)) if not col_data.isna().all() else None,
                    "q75": float(col_data.quantile(0.75)) if not col_data.isna().all() else None
                })
            else:
                # String statistics
                col_stats.update({
                    "most_common": str(col_data.mode()[0]) if len(col_data.mode()) > 0 else None,
                    "max_length": int(col_data.astype(str).str.len().max()) if not col_data.isna().all() else 0,
                    "min_length": int(col_data.astype(str).str.len().min()) if not col_data.isna().all() else 0,
                    "avg_length": float(col_data.astype(str).str.len().mean()) if not col_data.isna().all() else 0
                })
                
                # Add top values for categorical data
                if col_data.nunique() <= 20:
                    top_values = col_data.value_counts().head(10)
                    col_stats["top_values"] = [
                        {"value": str(val), "count": int(count)} 
                        for val, count in top_values.items()
                    ]
            
            stats[col] = self.convert_numpy_types(col_stats)
        
        return stats
    
    def generate_data_recommendations(self, df: pd.DataFrame, data_quality: Dict) -> List[str]:
        """Generate recommendations based on data analysis"""
        recommendations = []
        
        # Check for missing data
        missing_data = data_quality.get('missing_values', {})
        high_missing = [col for col, count in missing_data.items() if count > len(df) * 0.1]
        if high_missing:
            recommendations.append({
                "type": "warning",
                "title": "High Missing Data",
                "message": f"Columns with >10% missing data: {', '.join(high_missing)}",
                "action": "Consider imputation strategies or remove these columns"
            })
        
        # Check for low cardinality
        unique_counts = data_quality.get('unique_counts', {})
        low_cardinality = [col for col, count in unique_counts.items() if count == 1]
        if low_cardinality:
            recommendations.append({
                "type": "warning", 
                "title": "Constant Columns",
                "message": f"Columns with single value: {', '.join(low_cardinality)}",
                "action": "Consider removing constant columns as they provide no information"
            })
        
        # Check for potential IDs
        id_candidates = [col for col in df.columns if 'id' in col.lower() or 'number' in col.lower()]
        if id_candidates:
            recommendations.append({
                "type": "success",
                "title": "Potential Primary Keys",
                "message": f"Potential primary keys identified: {', '.join(id_candidates)}",
                "action": "Verify uniqueness and consider as primary keys"
            })
        
        # Check for high cardinality string columns
        high_cardinality = []
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio > 0.95 and len(df) > 100:
                    high_cardinality.append(col)
        
        if high_cardinality:
            recommendations.append({
                "type": "info",
                "title": "High Cardinality Columns",
                "message": f"Columns with high uniqueness: {', '.join(high_cardinality)}",
                "action": "Consider indexing these columns for better query performance"
            })
        
        # Data quality score assessment
        quality_score = data_quality.get('quality_score', 0)
        if quality_score >= 95:
            recommendations.append({
                "type": "success",
                "title": "Excellent Data Quality",
                "message": "Your data quality is excellent! No major issues detected.",
                "action": "Proceed with confidence to modernization"
            })
        elif quality_score >= 85:
            recommendations.append({
                "type": "info",
                "title": "Good Data Quality",
                "message": "Data quality is good with minor issues.",
                "action": "Review missing data patterns before production deployment"
            })
        else:
            recommendations.append({
                "type": "warning",
                "title": "Data Quality Needs Attention",
                "message": f"Data quality score: {quality_score}%. Consider data cleaning.",
                "action": "Implement data validation and cleaning procedures"
            })
        
        return recommendations
    
    def generate_microservices_architecture(self, df: pd.DataFrame) -> Dict:
        """Generate microservices recommendations based on data structure."""
        if df.empty:
            return {}
        
        services = []
        columns = [col.lower() for col in df.columns]
        
        # Service detection based on column patterns
        service_patterns = {
            "Customer Service": ["customer", "cust", "client"],
            "Employee Service": ["employee", "emp", "staff", "worker"],
            "Product Service": ["product", "item", "part", "inventory"],
            "Order Service": ["order", "transaction", "sale", "purchase"],
            "Payment Service": ["payment", "billing", "invoice", "amount"],
            "Address Service": ["address", "location", "city", "state", "zip"],
            "User Service": ["user", "login", "auth", "account"]
        }
        
        for service_name, patterns in service_patterns.items():
            if any(pattern in col for col in columns for pattern in patterns):
                services.append(service_name)
        
        # Default service if no patterns match
        if not services:
            services = ["Data Management Service"]
        
        return {
            "recommended_services": services,
            "total_services": len(services),
            "architecture_pattern": "Microservices with API Gateway"
        }

# Global data analysis service instance
data_service = DataAnalysisService()