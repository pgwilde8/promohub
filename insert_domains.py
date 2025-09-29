#!/usr/bin/env python3
"""
Helper script for inserting domains into PromoHub leads table

Usage:
    python insert_domains.py domain1.com domain2.com domain3.com
    python insert_domains.py --file domains.txt
    python insert_domains.py --csv leads.csv --domain-column=domain
"""

import sys
import csv
import asyncio
import logging
from pathlib import Path
from typing import List
import argparse

# Add the project root to path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.config import settings
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DomainInserter:
    """Helper class for inserting domains into leads table"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def insert_domains(self, domains: List[str], product: str = "ezclub", status: str = "new") -> int:
        """Insert domains into leads table"""
        inserted_count = 0
        
        for domain in domains:
            domain = domain.strip().lower()
            
            # Skip empty domains
            if not domain:
                continue
            
            # Remove protocol if present
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://', 1)[1]
            
            # Remove www if present  
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Remove trailing slash
            domain = domain.rstrip('/')
            
            try:
                # Check if domain already exists
                existing = self.db.execute(
                    text("SELECT id FROM leads WHERE domain = :domain"),
                    {"domain": domain}
                ).fetchone()
                
                if existing:
                    logger.info(f"Domain already exists: {domain}")
                    continue
                
                # Insert new lead with required columns
                self.db.execute(text("""
                    INSERT INTO leads (
                        owner_id, product_id, name, email, domain, status, lead_source, 
                        qualification_level, lead_score, verified, created_at
                    )
                    VALUES (
                        :owner_id, :product_id, :name, :email, :domain, :status, :lead_source, 
                        :qualification_level, :lead_score, :verified, NOW()
                    )
                """), {
                    "owner_id": 1,  # Default owner
                    "product_id": 1 if product == "ezclub" else 2,  # Default product mapping
                    "name": f"Lead from {domain}",  # Generate name from domain
                    "email": f"unknown@{domain}",  # Placeholder email to be enriched
                    "domain": domain,
                    "status": status,
                    "lead_source": f"{product}_domain_scraping",
                    "qualification_level": "unqualified",
                    "lead_score": 0,
                    "verified": False
                })
                
                self.db.commit()
                inserted_count += 1
                logger.info(f"Inserted domain: {domain}")
                
            except Exception as e:
                logger.error(f"Error inserting domain {domain}: {str(e)}")
                self.db.rollback()
        
        return inserted_count
    
    def insert_from_file(self, file_path: str, product: str = "ezclub") -> int:
        """Insert domains from a text file (one domain per line)"""
        try:
            with open(file_path, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Loading {len(domains)} domains from {file_path}")
            return self.insert_domains(domains, product)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return 0
    
    def insert_from_csv(self, csv_path: str, domain_column: str = "domain", product: str = "ezclub") -> int:
        """Insert domains from CSV file"""
        try:
            domains = []
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if domain_column in row and row[domain_column]:
                        domains.append(row[domain_column])
            
            logger.info(f"Loading {len(domains)} domains from CSV {csv_path}")
            return self.insert_domains(domains, product)
            
        except Exception as e:
            logger.error(f"Error reading CSV {csv_path}: {str(e)}")
            return 0
    
    def get_stats(self) -> dict:
        """Get current lead statistics"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_leads,
                    COUNT(CASE WHEN domain IS NOT NULL THEN 1 END) as has_domain,
                    COUNT(CASE WHEN email NOT LIKE 'unknown@%' AND email IS NOT NULL THEN 1 END) as has_email,
                    COUNT(CASE WHEN domain IS NOT NULL AND (email LIKE 'unknown@%' OR email IS NULL) THEN 1 END) as pending_enrichment
                FROM leads
            """)).fetchone()
            
            return {
                "total_leads": result.total_leads,
                "has_domain": result.has_domain,
                "has_email": result.has_email,
                "pending_enrichment": result.pending_enrichment
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}


def main():
    parser = argparse.ArgumentParser(description='Insert domains into PromoHub leads table')
    parser.add_argument('domains', nargs='*', help='Domain names to insert')
    parser.add_argument('--file', help='Text file with domains (one per line)')
    parser.add_argument('--csv', help='CSV file with domains')
    parser.add_argument('--domain-column', default='domain', help='Column name for domains in CSV')
    parser.add_argument('--product', default='ezclub', choices=['ezclub', 'ezdirectory'], 
                       help='Product to assign leads to')
    parser.add_argument('--stats', action='store_true', help='Show current statistics')
    
    args = parser.parse_args()
    
    with DomainInserter() as inserter:
        if args.stats:
            stats = inserter.get_stats()
            print("\n📊 Current Lead Statistics:")
            print(f"Total leads: {stats.get('total_leads', 0)}")
            print(f"With domain: {stats.get('has_domain', 0)}")
            print(f"With email: {stats.get('has_email', 0)}")
            print(f"Pending enrichment: {stats.get('pending_enrichment', 0)}")
            return
        
        total_inserted = 0
        
        # Insert from command line arguments
        if args.domains:
            logger.info(f"Inserting {len(args.domains)} domains from command line...")
            total_inserted += inserter.insert_domains(args.domains, args.product)
        
        # Insert from text file
        if args.file:
            logger.info(f"Inserting domains from file: {args.file}")
            total_inserted += inserter.insert_from_file(args.file, args.product)
        
        # Insert from CSV file
        if args.csv:
            logger.info(f"Inserting domains from CSV: {args.csv}")
            total_inserted += inserter.insert_from_csv(args.csv, args.domain_column, args.product)
        
        if not args.domains and not args.file and not args.csv:
            parser.print_help()
            return
        
        print(f"\n✅ Successfully inserted {total_inserted} new domains!")
        
        # Show updated stats
        stats = inserter.get_stats()
        print(f"\n📊 Updated Statistics:")
        print(f"Total leads: {stats.get('total_leads', 0)}")
        print(f"Pending enrichment: {stats.get('pending_enrichment', 0)}")
        
        if stats.get('pending_enrichment', 0) > 0:
            print(f"\n💡 Run the enrichment bot to populate emails for {stats['pending_enrichment']} leads")


if __name__ == "__main__":
    main()