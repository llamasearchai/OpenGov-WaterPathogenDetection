"""Batch import utilities for water samples and pathogen data."""

import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import structlog

from ..storage.water_sample_storage import WaterSampleStorage
from ..storage.pathogen_storage import PathogenStorage
from ..models.pathogen import PathogenCreate, PathogenType

logger = structlog.get_logger(__name__)


class BatchImporter:
    """Batch import data from CSV/Excel files."""

    def __init__(self):
        """Initialize batch importer."""
        self.sample_storage = WaterSampleStorage()
        self.pathogen_storage = PathogenStorage()

    def import_samples_from_csv(
        self,
        filepath: str,
        skip_errors: bool = True
    ) -> Tuple[int, int, List[str]]:
        """
        Import water samples from CSV file.
        
        Args:
            filepath: Path to CSV file
            skip_errors: Continue on errors (True) or fail fast (False)
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        successful = 0
        failed = 0
        errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    try:
                        # Validate required fields
                        required_fields = ['sample_id', 'location', 'collection_date', 
                                         'collector_name', 'sample_type']
                        missing_fields = [f for f in required_fields if not row.get(f)]
                        
                        if missing_fields:
                            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                        
                        # Prepare sample data
                        sample_data = {
                            'sample_id': row['sample_id'].strip(),
                            'location': row['location'].strip(),
                            'collection_date': row['collection_date'].strip(),
                            'collector_name': row['collector_name'].strip(),
                            'sample_type': row['sample_type'].strip(),
                        }
                        
                        # Add optional fields
                        if row.get('temperature'):
                            sample_data['temperature'] = float(row['temperature'])
                        if row.get('ph_level'):
                            sample_data['ph_level'] = float(row['ph_level'])
                        if row.get('turbidity'):
                            sample_data['turbidity'] = float(row['turbidity'])
                        if row.get('pathogen_id'):
                            sample_data['pathogen_id'] = row['pathogen_id'].strip()
                        if row.get('pathogen_concentration'):
                            sample_data['pathogen_concentration'] = float(row['pathogen_concentration'])
                        if row.get('test_date'):
                            sample_data['test_date'] = row['test_date'].strip()
                        if row.get('lab_technician'):
                            sample_data['lab_technician'] = row['lab_technician'].strip()
                        if row.get('notes'):
                            sample_data['notes'] = row['notes'].strip()
                        
                        # Create sample
                        self.sample_storage.create_sample(sample_data)
                        successful += 1
                        logger.info("sample_imported", row=row_num, sample_id=sample_data['sample_id'])
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error("import_row_failed", row=row_num, error=str(e))
                        
                        if not skip_errors:
                            raise ValueError(error_msg)
                
        except Exception as e:
            logger.error("csv_import_failed", filepath=filepath, error=str(e))
            raise
        
        logger.info("batch_import_completed", 
                   successful=successful, failed=failed, total=successful+failed)
        
        return successful, failed, errors

    def import_pathogens_from_csv(
        self,
        filepath: str,
        skip_errors: bool = True
    ) -> Tuple[int, int, List[str]]:
        """
        Import pathogens from CSV file.
        
        Args:
            filepath: Path to CSV file
            skip_errors: Continue on errors (True) or fail fast (False)
            
        Returns:
            Tuple of (successful_imports, failed_imports, error_messages)
        """
        successful = 0
        failed = 0
        errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Validate required fields
                        required_fields = ['id', 'name', 'pathogen_type']
                        missing_fields = [f for f in required_fields if not row.get(f)]
                        
                        if missing_fields:
                            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                        
                        # Prepare pathogen data
                        pathogen_data = {
                            'id': row['id'].strip(),
                            'name': row['name'].strip(),
                            'pathogen_type': PathogenType(row['pathogen_type'].strip().lower()),
                        }
                        
                        # Add optional fields
                        if row.get('common_name'):
                            pathogen_data['common_name'] = row['common_name'].strip()
                        if row.get('description'):
                            pathogen_data['description'] = row['description'].strip()
                        if row.get('symptoms'):
                            pathogen_data['symptoms'] = row['symptoms'].strip()
                        if row.get('transmission_route'):
                            pathogen_data['transmission_route'] = row['transmission_route'].strip()
                        if row.get('incubation_period_days'):
                            pathogen_data['incubation_period_days'] = int(row['incubation_period_days'])
                        if row.get('infectious_dose'):
                            pathogen_data['infectious_dose'] = row['infectious_dose'].strip()
                        
                        # Create pathogen
                        pathogen_create = PathogenCreate(**pathogen_data)
                        self.pathogen_storage.create_pathogen(pathogen_create)
                        successful += 1
                        logger.info("pathogen_imported", row=row_num, pathogen_id=pathogen_data['id'])
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error("import_pathogen_row_failed", row=row_num, error=str(e))
                        
                        if not skip_errors:
                            raise ValueError(error_msg)
                
        except Exception as e:
            logger.error("pathogen_csv_import_failed", filepath=filepath, error=str(e))
            raise
        
        logger.info("pathogen_batch_import_completed", 
                   successful=successful, failed=failed, total=successful+failed)
        
        return successful, failed, errors

    def generate_sample_csv_template(self, filepath: str) -> str:
        """
        Generate a CSV template for sample import.
        
        Args:
            filepath: Output file path
            
        Returns:
            Path to created template file
        """
        headers = [
            'sample_id', 'location', 'collection_date', 'collector_name',
            'sample_type', 'temperature', 'ph_level', 'turbidity',
            'pathogen_id', 'pathogen_concentration', 'test_date',
            'lab_technician', 'notes'
        ]
        
        example_data = {
            'sample_id': 'WS-2025-001',
            'location': 'North Treatment Plant',
            'collection_date': '2025-10-17',
            'collector_name': 'John Doe',
            'sample_type': 'raw_water',
            'temperature': '18.5',
            'ph_level': '7.2',
            'turbidity': '3.1',
            'pathogen_id': 'ECO-001',
            'pathogen_concentration': '150',
            'test_date': '2025-10-18',
            'lab_technician': 'Jane Smith',
            'notes': 'Routine monitoring sample'
        }
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(example_data)
        
        logger.info("sample_template_generated", filepath=filepath)
        return filepath

    def close(self) -> None:
        """Close storage connections."""
        self.sample_storage.close()
        self.pathogen_storage.close()

