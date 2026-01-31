"""
Schema Detector Module

Detects and classifies form types based on content analysis.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SchemaMatch:
    """Represents a schema detection match."""
    schema_type: str
    confidence: float
    matched_indicators: List[str]
    category: str


class SchemaDetector:
    """
    Detects and classifies form types based on content patterns.
    
    Supported form types:
    - Tax forms (W-2, W-4, 1099, 1040, etc.)
    - Medical forms (insurance claims, intake forms)
    - Employment forms (applications, onboarding, I-9)
    - Financial forms (loan applications, bank forms)
    - Legal forms (contracts, agreements)
    - Government forms (DMV, passport, visa)
    - Education forms (applications, transcripts)
    - Custom/Generic forms
    """
    
    def __init__(self):
        """Initialize schema detector with form patterns."""
        self.schemas = self._build_schema_definitions()
    
    def _build_schema_definitions(self) -> Dict[str, Dict]:
        """Build schema definitions with indicators."""
        return {
            # Tax Forms
            'w2': {
                'category': 'tax',
                'indicators': [
                    'wage and tax statement', 'w-2', 'form w-2',
                    'employer identification number', 'ein',
                    'employee\'s social security', 'federal income tax withheld',
                    'social security wages', 'medicare wages'
                ],
                'required_indicators': 2
            },
            'w4': {
                'category': 'tax',
                'indicators': [
                    'employee\'s withholding', 'w-4', 'form w-4',
                    'withholding allowance', 'personal allowances',
                    'additional amount to withhold'
                ],
                'required_indicators': 2
            },
            '1099': {
                'category': 'tax',
                'indicators': [
                    '1099', 'form 1099', 'miscellaneous income',
                    'nonemployee compensation', 'payer\'s federal',
                    'rents', 'royalties', 'other income'
                ],
                'required_indicators': 2
            },
            '1040': {
                'category': 'tax',
                'indicators': [
                    '1040', 'form 1040', 'u.s. individual income tax',
                    'adjusted gross income', 'taxable income',
                    'filing status', 'standard deduction', 'tax return'
                ],
                'required_indicators': 2
            },
            
            # Medical Forms
            'insurance_claim': {
                'category': 'medical',
                'indicators': [
                    'insurance claim', 'claim form', 'cms-1500', 'hcfa',
                    'diagnosis code', 'icd', 'cpt', 'procedure code',
                    'date of service', 'provider', 'patient information',
                    'policyholder', 'group number', 'member id'
                ],
                'required_indicators': 3
            },
            'medical_intake': {
                'category': 'medical',
                'indicators': [
                    'patient intake', 'medical history', 'health history',
                    'allergies', 'medications', 'emergency contact',
                    'primary care physician', 'insurance information',
                    'chief complaint', 'symptoms', 'family history'
                ],
                'required_indicators': 3
            },
            'hipaa_authorization': {
                'category': 'medical',
                'indicators': [
                    'hipaa', 'authorization', 'protected health information',
                    'phi', 'release of information', 'health information',
                    'disclose', 'privacy'
                ],
                'required_indicators': 3
            },
            
            # Employment Forms
            'job_application': {
                'category': 'employment',
                'indicators': [
                    'employment application', 'job application', 'applicant',
                    'position applied', 'work experience', 'previous employer',
                    'references', 'education history', 'equal opportunity',
                    'availability', 'desired salary'
                ],
                'required_indicators': 3
            },
            'i9': {
                'category': 'employment',
                'indicators': [
                    'i-9', 'form i-9', 'employment eligibility',
                    'verification', 'citizenship status', 'work authorization',
                    'list a', 'list b', 'list c', 'uscis'
                ],
                'required_indicators': 3
            },
            'onboarding': {
                'category': 'employment',
                'indicators': [
                    'new hire', 'onboarding', 'employee information',
                    'start date', 'department', 'manager', 'direct deposit',
                    'emergency contact', 'benefits enrollment'
                ],
                'required_indicators': 3
            },
            
            # Financial Forms
            'loan_application': {
                'category': 'financial',
                'indicators': [
                    'loan application', 'credit application', 'borrower',
                    'loan amount', 'interest rate', 'collateral',
                    'monthly payment', 'debt-to-income', 'credit score',
                    'assets', 'liabilities', 'loan purpose'
                ],
                'required_indicators': 3
            },
            'bank_account': {
                'category': 'financial',
                'indicators': [
                    'account opening', 'new account', 'account application',
                    'checking', 'savings', 'routing number', 'account number',
                    'joint account', 'beneficiary', 'initial deposit'
                ],
                'required_indicators': 3
            },
            
            # Legal Forms
            'contract': {
                'category': 'legal',
                'indicators': [
                    'agreement', 'contract', 'parties', 'terms and conditions',
                    'whereas', 'hereby', 'binding', 'effective date',
                    'termination', 'governing law', 'jurisdiction',
                    'indemnification', 'liability'
                ],
                'required_indicators': 3
            },
            'power_of_attorney': {
                'category': 'legal',
                'indicators': [
                    'power of attorney', 'attorney-in-fact', 'principal',
                    'agent', 'authority', 'durable', 'revocation',
                    'notarized', 'witness'
                ],
                'required_indicators': 3
            },
            
            # Government Forms
            'dmv': {
                'category': 'government',
                'indicators': [
                    'dmv', 'driver license', 'vehicle registration',
                    'title', 'vin', 'license plate', 'odometer',
                    'registration fee', 'department of motor vehicles'
                ],
                'required_indicators': 3
            },
            'passport': {
                'category': 'government',
                'indicators': [
                    'passport', 'citizenship', 'place of birth',
                    'passport number', 'nationality', 'travel document',
                    'department of state', 'ds-11', 'ds-82'
                ],
                'required_indicators': 3
            },
            
            # Education Forms
            'school_application': {
                'category': 'education',
                'indicators': [
                    'admission', 'application', 'enrollment', 'student',
                    'gpa', 'transcript', 'academic', 'school',
                    'grade level', 'program', 'degree', 'major'
                ],
                'required_indicators': 3
            },
            'financial_aid': {
                'category': 'education',
                'indicators': [
                    'fafsa', 'financial aid', 'student aid', 'grant',
                    'scholarship', 'loan', 'efc', 'expected family contribution',
                    'award letter', 'disbursement'
                ],
                'required_indicators': 3
            }
        }
    
    def detect(self, text: str, fields: Dict[str, Any] = None) -> Optional[str]:
        """
        Detect form schema type.
        
        Args:
            text: Raw form text
            fields: Optional extracted fields
            
        Returns:
            Detected schema type or None
        """
        match = self.detect_with_confidence(text, fields)
        return match.schema_type if match and match.confidence >= 0.5 else None
    
    def detect_with_confidence(self, text: str, 
                               fields: Dict[str, Any] = None) -> Optional[SchemaMatch]:
        """
        Detect form schema with confidence score.
        
        Args:
            text: Raw form text
            fields: Optional extracted fields
            
        Returns:
            SchemaMatch object or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Add fields to search text
        if fields:
            field_text = ' '.join(str(k) + ' ' + str(v) for k, v in fields.items())
            text_lower += ' ' + field_text.lower()
        
        best_match = None
        best_score = 0
        
        for schema_type, schema_def in self.schemas.items():
            matched_indicators = []
            
            for indicator in schema_def['indicators']:
                if indicator in text_lower:
                    matched_indicators.append(indicator)
            
            if len(matched_indicators) >= schema_def['required_indicators']:
                # Calculate confidence score
                score = len(matched_indicators) / len(schema_def['indicators'])
                
                if score > best_score:
                    best_score = score
                    best_match = SchemaMatch(
                        schema_type=schema_type,
                        confidence=min(1.0, score * 1.2),  # Boost slightly
                        matched_indicators=matched_indicators,
                        category=schema_def['category']
                    )
        
        return best_match
    
    def detect_all_matches(self, text: str, 
                           fields: Dict[str, Any] = None) -> List[SchemaMatch]:
        """
        Find all matching schemas with confidence scores.
        
        Args:
            text: Raw form text
            fields: Optional extracted fields
            
        Returns:
            List of SchemaMatch objects sorted by confidence
        """
        if not text:
            return []
        
        text_lower = text.lower()
        
        if fields:
            field_text = ' '.join(str(k) + ' ' + str(v) for k, v in fields.items())
            text_lower += ' ' + field_text.lower()
        
        matches = []
        
        for schema_type, schema_def in self.schemas.items():
            matched_indicators = []
            
            for indicator in schema_def['indicators']:
                if indicator in text_lower:
                    matched_indicators.append(indicator)
            
            if matched_indicators:
                score = len(matched_indicators) / len(schema_def['indicators'])
                matches.append(SchemaMatch(
                    schema_type=schema_type,
                    confidence=min(1.0, score * 1.2),
                    matched_indicators=matched_indicators,
                    category=schema_def['category']
                ))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)
    
    def get_schema_info(self, schema_type: str) -> Optional[Dict]:
        """
        Get information about a schema type.
        
        Args:
            schema_type: Schema type identifier
            
        Returns:
            Schema definition or None
        """
        return self.schemas.get(schema_type)
    
    def get_expected_fields(self, schema_type: str) -> List[str]:
        """
        Get expected fields for a schema type.
        
        Args:
            schema_type: Schema type identifier
            
        Returns:
            List of expected field names
        """
        expected_fields = {
            'w2': [
                'Employee SSN', 'Employer EIN', 'Employee Name',
                'Employer Name', 'Wages', 'Federal Tax Withheld',
                'Social Security Wages', 'Medicare Wages'
            ],
            'insurance_claim': [
                'Patient Name', 'Date of Birth', 'Insurance ID',
                'Group Number', 'Provider Name', 'Date of Service',
                'Diagnosis Code', 'Procedure Code', 'Amount Charged'
            ],
            'job_application': [
                'Applicant Name', 'Address', 'Phone', 'Email',
                'Position Applied For', 'Desired Salary',
                'Work Experience', 'Education', 'References'
            ],
            'loan_application': [
                'Borrower Name', 'SSN', 'Address', 'Employment',
                'Annual Income', 'Loan Amount', 'Loan Purpose',
                'Assets', 'Liabilities'
            ]
        }
        
        return expected_fields.get(schema_type, [])
    
    def validate_fields(self, schema_type: str, 
                        fields: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Validate extracted fields against expected schema.
        
        Args:
            schema_type: Schema type identifier
            fields: Extracted fields
            
        Returns:
            Tuple of (completeness score, missing fields)
        """
        expected = self.get_expected_fields(schema_type)
        
        if not expected:
            return 1.0, []
        
        field_names_lower = [k.lower() for k in fields.keys()]
        
        found = 0
        missing = []
        
        for expected_field in expected:
            expected_lower = expected_field.lower()
            
            # Check for exact or partial match
            matched = any(
                expected_lower in f or f in expected_lower
                for f in field_names_lower
            )
            
            if matched:
                found += 1
            else:
                missing.append(expected_field)
        
        completeness = found / len(expected)
        
        return completeness, missing
